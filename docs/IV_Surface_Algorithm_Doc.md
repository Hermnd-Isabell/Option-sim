# IMPLIES VOLATILITY & SURFACE ALGORITHM DOCUMENTATION
# 隐含波动率与波动率曲面生成算法文档

本文档详细说明了 HyperQuant AI 平台中 IV 微笑曲线 (IV Smile) 与 3D 波动率曲面 (Volatility Surface) 的生成逻辑与核心算法。

## 1. 核心模型：隐含波动率 (Implied Volatility)

所有曲面的基础是单个期权合约的隐含波动率计算。

### 1.1 计算原理
我们使用 **Newton-Raphson (牛顿-拉夫逊法)** 数值求解 BSM (Black-Scholes-Merton) 反函数。

$$ C_{mkt} = BSM(S, K, T, r, q, \sigma_{imp}) $$

其中：
- $C_{mkt}$: 市场价格
- $S$: 标的即期价格 (Underlying Spot)
- $K$: 行权价 (Strike)
- $T$: 剩余期限 (Time to Expiry, in years)
- $r$: 无风险利率 (Risk-free Rate)
- $q$: 分红率 (Dividend Yield)

### 1.2 求解算法 (Backend: `pricing.py`)
为了保证大规模计算 (<10ms/1000合约) 的性能，我们使用 **Numba** 进行了向量化加速。

1.  **初始猜测 (Initial Guess)**: 使用 Brenner-Subrahmanyam 近似公式快速锁定初始值。
    $$ \sigma_0 \approx \sqrt{\frac{2\pi}{T}} \frac{C}{S} $$
2.  **迭代 (Iteration)**:
    $$ \sigma_{n+1} = \sigma_n - \frac{BSM(\sigma_n) - C_{mkt}}{Vega(\sigma_n)} $$
3.  **兜底机制 (Fallback)**: 当 Vega 接近 0 (深实值/虚值) 导致牛顿法不收敛时，自动降级为 **Bisection (二分法)** 求解，确保 100% 的求解成功率。

---

## 2. IV 微笑曲线 (IV Smile Curve)

IV 微笑曲线展示了**同一到期日**下，不同行权价 ($K$) 对应的波动率结构。

### 2.1 数据清洗与选择 (Frontend Logic)
为了避免"锯齿状" (Jagged) 曲线，系统采用了**智能合约选择 (Smart Expiry Selection)** 逻辑：

1.  **分组**: 将所有期权按到期日分组。
2.  **筛选**: 剔除流动性不足 (合约数 < 10) 的月份。
3.  **近月优先 (Nearest Priority)**: 按 $DTE$ (Days to Expiry) 排序，优先选择最近月份。
4.  **移仓换月 (Roll-over Mechanism)**:
    -   如果最近月份 $DTE < 3$ 天（临近交割，数据噪音大），自动跳过。
    -   选择**次近月 (Next Month)** 作为主力展示合约。

### 2.2 曲线平滑 (Smoothing - SVI Model)
虽然前端直接展示市场 IV，但后端 (`data.py`) 会尝试使用 **SVI (Stochastic Volatility Inspired)** 模型对原始数据进行拟合，去除市场噪音。

**SVI Raw 参数化公式**:
$$ w(k) = a + b \left( \rho(k - m) + \sqrt{(k - m)^2 + \sigma^2} \right) $$

- $k = \ln(K/F)$: 对数带钱度 (Log-moneyness)
- $w = \sigma_{BS}^2 T$: 总方差
- $m, \sigma$: 决定微笑的中心与宽度
- $\rho$: 决定偏度 (Skew)，即曲线左右倾斜程度
- $a, b$: 决定水平高度与开口大小

如果 SVI 拟合失败（如数据点过少），系统会退化使用 **UnivariateSpline (单变量样条)** 进行平滑。

---

## 3. 3D 波动率曲面 (Volatility Surface)

波动率曲面是关于 **(行权价, 到期时间, 隐含波动率)** 的三维结构。

### 3.1 网格构建 (Grid Construction)
为了在前端绘制整齐的 3D 曲面，我们需要讲离散的市场数据映射到规则网格上：

1.  **X轴 (Strikes)**: 提取市场所有有效行权价，并进行归一化或插值生成固定步长的网格（通常25个点）。
2.  **Y轴 (DTE)**: 定义标准期限结构，例如 `[10, 30, 60, 90, 120, 150, 180]` 天。
3.  **Z轴 (IV)**: 计算每个 (Strike, DTE) 网格点的理论 IV 值。

### 3.2 插值与外推 (Interpolation)
由于市场数据在时间和行权价上都是离散的，我们需要填补空缺：

-   **行权价维度 (Strike Dimension)**: 对每个期限切片，优先使用 SVI 模型计算该 DTE 下任意 K 的理论 IV。
-   **时间维度 (Time Dimension)**: 
    -   如果在两个实际到期日之间（例如 DTE=45，介于30天与60天合约之间），使用 **线性插值 (Linear Interpolation)** 或 **方差插值 (Total Variance Interpolation)**。
        $$ \sigma^2_{45} T_{45} \approx \frac{(T_{60}-T_{45}) \sigma^2_{30}T_{30} + (T_{45}-T_{30})\sigma^2_{60}T_{60}}{T_{60}-T_{30}} $$

### 3.3 前端渲染 (Frontend Visualization)
前端使用 `Plotly.js` (via `react-plotly.js`) 的 `surface` 图表类型进行渲染。

-   **光照效果**:配置 Ambient/Diffuse/Specular 光照参数，增强 3D 立体感。
-   **交互**: 支持鼠标旋转、缩放。
-   **热力图投影**: 在 Z 轴底部投影等高线 (Contour)，方便查看 IV 聚集区域。

---

## 4. 优化案例分析：解决"锯齿状"曲线 (Refinement Case Study - 2D)

本节记录了 2D IV 微笑曲线从问题发现到解决的完整过程。

### 4.1 问题现象 (The Issue)
在初始版本中，当用户在全局筛选器中设置由 "到期日 = 全部 (All)" 时，IV 微笑曲线呈现剧烈的 **锯齿状 (Jagged/Zigzag)** 形态。

**原因分析**: 不同到期日 (Tenor) 的期权在同一行权价下有不同的隐含波动率 (期限结构)。混合显示会导致连线跳跃。

### 4.2 解决方案 (The Fix)
我们引入了 **智能合约筛选 (Smart Selection) + 移仓逻辑 (Rollover)**。

1.  **近月优先**: 优先展示最近到期的主力合约。
2.  **3天移仓**: 当近月合约 DTE < 3 天时，自动切换至次近月，避免临期噪音。

---

## 5. 3D 曲面如何解决锯齿问题？ (3D Surface Smoothing)

用户经常会问："既然 2D 曲线需要通过'只选一个日期'来避免锯齿，那 3D 曲面包含了所有日期，为什么它是平滑的？"

这得益于我们针对 3D 曲面采用的**完全不同的处理机制**：

### 5.1 区别核心
-   **2D 曲线 (Raw Data)**: 直接展示**市场原始数据**。为了保真，我们不修改数据点，只能通过"筛选"来避免视觉混乱。
-   **3D 曲面 (Modeled Data)**: 展示的是**数学模型拟合后的理论曲面**。我们对原始数据进行了**重建 (Reconstruction)**。

### 5.2 抗锯齿"三板斧"
我们在后端 `data.py` 中实施了三个步骤来确保曲面平滑：

1.  **SVI 参数化拟合 (SVI Optimization)**:
    -   对于每一个到期日切片 (Slice)，我们不使用原始 IV 点，而是用 **SVI 模型** 去拟合这些点。
    -   SVI 模型本身就是一条平滑的抛物线/双曲线，天生没有锯齿。
    -   **结果**: 无论市场报价中有多少噪音或异常跳动，模型输出的永远是一条完美的微笑曲线。

2.  **隐含即期价格对齐 (Implied Spot Alignment)**:
    -   锯齿的另一个来源是 Forward Price (远期价格) 的错误估计。
    -   Code L840: 我们利用 Put-Call Parity 为每个期限单独反向计算 **Implied Spot**。
    -   这确保了不同期限的平值点 (ATM) 是该期限下真实的平值点，消除了期限结构错位带来的"伪锯齿"。

3.  **规则网格重采样 (Grid Resampling)**:
    -   市场上的行权价是杂乱的 (e.g., 2.98, 2.99, 3.00...)。
    -   我们构建了一个标准的 $25 \times 10$ 网格。
    -   利用拟合好的 SVI 参数，计算这些标准网格点上的理论 IV。
    -   **效果**: 最终渲染的是一个整齐的网格，而不是杂乱的散点，通过 Grid Linear Interpolation 形成的曲面自然如丝般顺滑。

**总结**: 2D 曲线靠**"选"** (Selection) 来规避冲突，3D 曲面靠**"算"** (Modeling) 来融合数据。

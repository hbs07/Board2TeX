# Board2TeX 自动评估报告

> 生成时间: 2026-11-21 11:23
> 数据: `assets/eval/` 的合成板书(纯白底、印刷体、无透视)。
> **口径说明**:这组数字衡量的是算法链路是否正确,不代表手机实拍效果;
> 实拍可用率请用 `--mode manual` 按 `eval/labels.csv` 统计。

## 汇总

| 指标 | 数值 |
|---|---|
| 图片数 | 4 |
| 总行数 | 15 |
| 行数完全正确 | 100% |
| 行分类准确率 | 100.0% |
| 文字行 CER(越低越好) | 1.3% |
| 文字行完全正确 | 67% |
| 公式行完全匹配 | 50% |
| 公式行相似度(1 - CER) | 64.3% |

## 逐图明细

| 图片 | 期望行/实际行 | 行数 | 分类准确 | 文字 CER | 公式完全匹配 |
|---|---|---|---|---|---|
| board_01.png | 5/5 | OK | 5/5 | 0.9% | 1/2 |
| board_02.png | 4/4 | OK | 4/4 | 0.7% | 1/1 |
| board_03.png | 4/4 | OK | 4/4 | 0.0% | 1/2 |
| board_04.png | 2/2 | OK | 2/2 | 7.1% | 0/1 |

## 逐行明细

### board_01.png

| # | 期望 | 预测 | 结果 |
|---|---|---|---|
| 0 | `Derivative Rules` | `Derivative Rules` | CER 0% |
| 1 | `Given two functions f and g, we have:` | `Given two functions f and g,we have:` | CER 3% |
| 2 | `\fracddxx^2=2x` | `\fracddxX^2=2X` | 相似 86% |
| 3 | `\int_0^1x^2dx=\frac13` | `\int_0^1x^2dx=\frac13` | 完全匹配 |
| 4 | `The chain rule composes the two derivatives` | `The chain rule composes the two derivatives` | CER 0% |

### board_02.png

| # | 期望 | 预测 | 结果 |
|---|---|---|---|
| 0 | `Matrix Multiplication` | `Matrix Multiplication` | CER 0% |
| 1 | `The product of two matrices is defined as:` | `The product of two matrices is defined as:` | CER 0% |
| 2 | `(AB)_ij=\sum_kA_ikB_kj` | `(AB)_ij=\sum_kA_ikB_kj` | 完全匹配 |
| 3 | `The identity matrix leaves every vector unchanged` | `The identitymatrix leaves every vector unchanged` | CER 2% |

### board_03.png

| # | 期望 | 预测 | 结果 |
|---|---|---|---|
| 0 | `Limits` | `Limits` | CER 0% |
| 1 | `\lim_x\to0\frac\sinxx=1` | `\lim_x\to0\frac\sinxx=1` | 完全匹配 |
| 2 | `A function is continuous when the limit equals the value` | `A function is continuous when the limit equals the value` | CER 0% |
| 3 | `f'(x)=\lim_h\to0\fracf(x+h)-f(x)h` | `f'(X)=|i||||||||||||||||<\cdot+h|\rangle-f(\chi)` | 相似 0% |

### board_04.png

| # | 期望 | 预测 | 结果 |
|---|---|---|---|
| 0 | `Euler Identity` | `EulerIdentity` | CER 7% |
| 1 | `e^i\pi+1=0` | `\Theta^I/T\mathbb+1\supset\emptyset` | 相似 0% |

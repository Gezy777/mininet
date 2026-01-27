from typing import List
import matplotlib.pyplot as plt

# 这是一个用于Matplotlib绘图的工具类
# 通过调用这个类更便捷地自定义生成图表
# 画图教程
class SimulatePlt:
    def __init__(self):
        self.default_figsize = (14, 12)

    def simple_plot(self, x, y, output_file, title, xlabel, ylabel):
        # 定义画布的大小
        plt.figure(figsize=self.default_figsize)

        # 绘制简单折线图，每个点用圆圈标记
        plt.plot(x, y, marker='o')

        # 添加标题和坐标轴
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        # 显示网格
        plt.grid(True)

        # 保存图表到指定文件
        plt.savefig(output_file)
        
        # 关闭图表，释放内存
        plt.close()


import matplotlib.pyplot as plt

# 创建 3 行 1 列的子图，图形尺寸为 14x12 英寸，子图共享 x 轴
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# 绘制第一个子图
axes[0].plot([1, 2, 3], [1, 4, 9], label="Plot 1")
axes[0].set_title("Subplot 1")

# 绘制第二个子图
axes[1].plot([1, 2, 3], [1, 2, 3], label="Plot 2", color='r')
axes[1].set_title("Subplot 2")

# 绘制第三个子图
axes[2].plot([1, 2, 3], [9, 4, 1], label="Plot 3", color='g')
axes[2].set_title("Subplot 3")

# 设置 x 轴的标签
axes[2].set_xlabel("X Axis Label")

# 设置 y 轴的标签
axes[1].set_ylabel("Y Axis Label")

# 显示图形
plt.tight_layout()  # 调整子图之间的间距

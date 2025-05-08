# 安装必要的包
# pip install skyfield tzwhere geopy matplotlib numpy pytz

import datetime
from geopy.geocoders import Nominatim
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 必须在导入 pyplot 之前设置
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84, utc, Star
from skyfield.data import hipparcos, stellarium
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.units import Distance
from skyfield.timelib import Time
import io
from PIL import Image
import pytz
import matplotlib.font_manager as fm
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS 自带的支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def parse_constellation_lines(filename):
    constellations = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 3:  # 跳过无效行
                continue
            name = parts[0]
            count = int(parts[1])
            stars = [int(x) for x in parts[2:]]
            edges = []
            for i in range(0, len(stars)-1, 2):
                edges.append((stars[i], stars[i+1]))
            constellations.append((name, edges))
    return constellations

def load_data():
    # 加载天文数据
    eph = load('de421.bsp')
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)
    # 创建Star对象
    stars = Star.from_dataframe(df)
    
    # 加载星座连线数据
    try:
        constellations = parse_constellation_lines('constellationship.fab')
    except Exception as e:
        print(f"无法加载星座数据：{str(e)}")
        constellations = []
    
    return eph, stars, df, constellations

def collect_celestial_data(location, when, transparent=True):
    # 获取地理位置
    geolocator = Nominatim(user_agent="my_agent", timeout=10)  # 增加超时时间到10秒
    try:
        location_data = geolocator.geocode(location)
        if location_data is None:
            raise ValueError(f"无法找到位置: {location}")
    except Exception as e:
        print(f"获取地理位置时出错: {str(e)}")
        print("使用默认位置（北京）")
        location_data = type('Location', (), {'latitude': 39.9042, 'longitude': 116.4074})()
    
    # 创建观察者位置
    observer = wgs84.latlon(location_data.latitude, location_data.longitude)
    
    # 解析时间
    if isinstance(when, str):
        when = datetime.datetime.strptime(when, '%Y-%m-%d %H:%M:%S')
    
    # 创建时间对象
    ts = load.timescale()
    t = ts.from_datetime(when)
    
    # 加载数据
    eph, stars, df, constellations = load_data()
    
    # 计算恒星位置
    earth = eph['earth']
    topos = earth + observer
    star_positions = topos.at(t).observe(stars)
    
    # 获取恒星坐标
    alt, az, distance = star_positions.apparent().altaz()
    
    # 过滤可见的恒星
    visible = alt.degrees > 0
    
    # 根据星等筛选恒星（只显示亮度较高的恒星）
    limiting_magnitude = 6.5  # 使用6.5等作为限制
    magnitudes = df['magnitude'].values
    bright_stars = magnitudes <= limiting_magnitude
    
    # 先应用可见性条件
    visible_alt = alt.degrees[visible]
    visible_az = az.degrees[visible]
    visible_magnitudes = magnitudes[visible]
    visible_indices = np.where(visible)[0]
    
    # 再应用亮度条件
    bright = visible_magnitudes <= limiting_magnitude
    visible_alt = visible_alt[bright]
    visible_az = visible_az[bright]
    visible_magnitudes = visible_magnitudes[bright]
    visible_indices = visible_indices[bright]
    
    # 创建图形
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    
    # 移除边缘线
    ax.spines['polar'].set_visible(False)
    
    # 绘制星座连线
    for name, edges in constellations:
        for star1, star2 in edges:
            try:
                # 检查恒星是否在数据集中且够亮
                if star1 not in df.index or star2 not in df.index:
                    continue
                if df.loc[star1, 'magnitude'] > limiting_magnitude or df.loc[star2, 'magnitude'] > limiting_magnitude:
                    continue
                
                # 获取恒星索引
                idx1 = df.index.get_loc(star1)
                idx2 = df.index.get_loc(star2)
                
                # 检查恒星是否可见
                if idx1 not in visible_indices or idx2 not in visible_indices:
                    continue
                
                # 获取可见数组中的位置
                pos1 = np.where(visible_indices == idx1)[0][0]
                pos2 = np.where(visible_indices == idx2)[0][0]
                
                # 绘制连线
                ax.plot([np.radians(visible_az[pos1]), np.radians(visible_az[pos2])],
                       [90 - visible_alt[pos1], 90 - visible_alt[pos2]],
                       color='#ffff', linewidth=0.4, alpha=0.5, zorder=1)
            except (KeyError, IndexError, ValueError):
                continue
    
    # 使用原始代码中的恒星大小计算方法
    max_star_size = 40  # 最大恒星大小
    # 基于平方根的缩放
    raw_size = np.sqrt(10 ** (visible_magnitudes / -2.5))
    # 线性修正
    correction_factor = 1 - 0.15 * visible_magnitudes  # 使用原始代码中的系数
    # 结合两者
    sizes = max_star_size * raw_size * correction_factor
    
    # 绘制恒星
    scatter = ax.scatter(np.radians(visible_az), 90 - visible_alt,
                        c='white', s=sizes, alpha=1.0, marker='o',
                        linewidths=0, zorder=2)
    
    # 添加方位标记
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 90)
    ax.set_rticks([])  # 移除刻度
    ax.set_rlabel_position(0)
    
    # 移除网格线和方位标记
    ax.grid(False)
    ax.set_xticklabels([])  # 移除方位标记
    
    # 设置背景颜色
    if transparent:
        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
    else:
        ax.set_facecolor('#041A40')
        fig.patch.set_facecolor('#041A40')
    
    # 设置标题
    plt.title(f'星空图 - {location}\n{when.strftime("%Y-%m-%d %H:%M:%S")}', 
              color='white', pad=20)
    
    # 保存图像
    buf = io.BytesIO()
    plt.savefig(buf, format='png', 
                facecolor='none' if transparent else '#041A40',
                edgecolor='none', 
                bbox_inches='tight', 
                dpi=400, 
                transparent=transparent)
    buf.seek(0)
    plt.close()
    
    return Image.open(buf)

class StarMapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("星图生成器")
        self.root.geometry("400x500")
        
        # 设置样式
        style = ttk.Style()
        style.configure('TLabel', padding=5)
        style.configure('TButton', padding=5)
        style.configure('TEntry', padding=5)
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 位置输入
        ttk.Label(main_frame, text="位置（城市名）:").grid(row=0, column=0, sticky=tk.W)
        self.location_var = tk.StringVar(value="北京")
        ttk.Entry(main_frame, textvariable=self.location_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # 日期输入
        ttk.Label(main_frame, text="日期 (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W)
        beijing_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.datetime.now(beijing_tz)
        self.date_var = tk.StringVar(value=current_time.strftime("%Y-%m-%d"))
        ttk.Entry(main_frame, textvariable=self.date_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        # 时间输入
        ttk.Label(main_frame, text="时间 (HH:MM):").grid(row=2, column=0, sticky=tk.W)
        self.time_var = tk.StringVar(value=current_time.strftime("%H:%M"))
        ttk.Entry(main_frame, textvariable=self.time_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        # 透明背景选项
        self.transparent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="透明背景", variable=self.transparent_var).grid(row=3, column=0, columnspan=2, pady=10)
        
        # 生成按钮
        ttk.Button(main_frame, text="生成星图", command=self.generate_star_map).grid(row=4, column=0, columnspan=2, pady=20)
        
        # 状态标签
        self.status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=2, pady=10)
        
        # 设置列权重
        main_frame.columnconfigure(1, weight=1)
    
    def generate_star_map(self):
        try:
            # 获取输入值
            location = self.location_var.get()
            date = self.date_var.get()
            time = self.time_var.get()
            transparent = self.transparent_var.get()
            
            # 组合日期和时间，并添加时区信息
            beijing_tz = pytz.timezone('Asia/Shanghai')
            when_str = f"{date} {time}:00"
            when = datetime.datetime.strptime(when_str, '%Y-%m-%d %H:%M:%S')
            when = beijing_tz.localize(when)
            
            # 更新状态
            self.status_var.set("正在生成星图...")
            self.root.update()
            
            # 生成星图
            star_map = collect_celestial_data(location, when, transparent)
            
            # 保存图像
            star_map.save('star_map.png')
            
            self.status_var.set("星图已保存为 star_map.png")
            messagebox.showinfo("成功", "星图已生成！")
            
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
            messagebox.showerror("错误", str(e))

def main():
    root = tk.Tk()
    app = StarMapGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
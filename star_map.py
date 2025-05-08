# 安装必要的包
# pip install skyfield tzwhere geopy matplotlib numpy pytz

import datetime
from geopy.geocoders import Nominatim
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 必须在导入 pyplot 之前设置
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84, utc, Star
from skyfield.data import hipparcos
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN
from skyfield.units import Distance
from skyfield.timelib import Time
import io
from PIL import Image
import pytz
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 只使用微软雅黑
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 全局缓存
_eph = None
_stars = None
_df = None
_constellations = None

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
    global _eph, _stars, _df, _constellations
    
    # 如果已经加载过数据，直接返回缓存
    if _eph is not None and _stars is not None and _df is not None and _constellations is not None:
        return _eph, _stars, _df, _constellations
    
    # 加载天文数据
    _eph = load('de421.bsp')
    try:
        # 尝试从本地文件加载
        with open('hip_main.dat', 'rb') as f:
            _df = hipparcos.load_dataframe(f)
            # 只保留亮度大于6.5等的恒星
            _df = _df[_df['magnitude'] <= 6.5]
    except Exception as e:
        print(f"无法从本地加载星表数据：{str(e)}")
        print("尝试从网络加载...")
        try:
            # 如果本地加载失败，尝试从网络加载
            with load.open(hipparcos.URL) as f:
                _df = hipparcos.load_dataframe(f)
                # 只保留亮度大于6.5等的恒星
                _df = _df[_df['magnitude'] <= 6.5]
        except Exception as e:
            print(f"无法从网络加载星表数据：{str(e)}")
            raise
    
    # 创建Star对象
    _stars = Star.from_dataframe(_df)
    
    # 加载星座连线数据
    try:
        _constellations = parse_constellation_lines('constellationship.fab')
    except Exception as e:
        print(f"无法加载星座数据：{str(e)}")
        _constellations = []
    
    return _eph, _stars, _df, _constellations

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
    
    # 获取可见的恒星数据
    visible_alt = alt.degrees[visible]
    visible_az = az.degrees[visible]
    visible_magnitudes = df['magnitude'].values[visible]
    visible_indices = np.where(visible)[0]
    
    # 创建图形
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    
    # 移除边缘线
    ax.spines['polar'].set_visible(False)
    
    # 绘制星座连线
    for name, edges in constellations:
        for star1, star2 in edges:
            try:
                # 检查恒星是否在数据集中
                if star1 not in df.index or star2 not in df.index:
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
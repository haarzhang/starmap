# 安装必要的包
# pip install skyfield tzwhere geopy matplotlib numpy pytz

import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from tzwhere import tzwhere
import io
import hipparcos
import stellarium

def load_data():
    """加载天文数据"""
    # 加载星表数据
    stars = hipparcos.load('hip_main.dat')
    
    # 加载星座连线数据
    try:
        constellations = stellarium.load('constellationship.fab')
    except:
        print("无法加载星座数据，将不显示星座连线")
        constellations = []
    
    return stars, constellations

def collect_celestial_data(location, when, transparent=False):
    """收集天文数据并生成星图"""
    # 获取地理位置
    geolocator = Nominatim(user_agent="my_star_map")
    location_data = geolocator.geocode(location)
    if location_data is None:
        raise ValueError(f"无法找到位置: {location}")
    
    # 获取时区
    tz = tzwhere.tzwhere()
    timezone_str = tz.tzNameAt(location_data.latitude, location_data.longitude)
    if timezone_str is None:
        timezone_str = 'UTC'
    timezone = pytz.timezone(timezone_str)
    
    # 转换时间到时区
    if when.tzinfo is None:
        when = timezone.localize(when)
    
    # 加载星表数据
    stars, constellations = load_data()
    
    # 创建图形
    fig = plt.figure(figsize=(10, 10), facecolor='none' if transparent else '#041A40')
    ax = fig.add_subplot(111, projection='polar')
    
    # 设置背景颜色
    if not transparent:
        ax.set_facecolor('#041A40')
    
    # 移除网格线和方位标记
    ax.grid(False)
    ax.set_xticklabels([])
    ax.spines['polar'].set_visible(False)
    
    # 计算恒星位置
    ts = load.timescale()
    t = ts.from_datetime(when)
    earth = load('de421.bsp')['earth']
    
    # 获取观察者位置
    observer = wgs84.latlon(location_data.latitude, location_data.longitude)
    
    # 计算恒星位置
    for star in stars:
        if star.magnitude <= 6.5:  # 只显示6.5等以上的恒星
            ra = np.radians(star.ra)
            dec = np.radians(star.dec)
            
            # 计算方位角和高度
            alt, az = observer.at(t).observe(earth).apparent().altaz()
            
            # 只绘制在地平线以上的恒星
            if alt.degrees > 0:
                # 根据星等调整点的大小
                size = 50 * (7 - star.magnitude) / 7
                ax.scatter(ra, 90 - dec, s=size, color='white', alpha=1.0)
    
    # 绘制星座连线
    for constellation in constellations:
        for edge in constellation.edges:
            star1 = stars[edge[0]]
            star2 = stars[edge[1]]
            
            # 检查两颗星是否都可见
            if star1.magnitude <= 6.5 and star2.magnitude <= 6.5:
                ra1 = np.radians(star1.ra)
                dec1 = np.radians(star1.dec)
                ra2 = np.radians(star2.ra)
                dec2 = np.radians(star2.dec)
                
                # 计算两颗星的高度
                alt1, _ = observer.at(t).observe(earth).apparent().altaz()
                alt2, _ = observer.at(t).observe(earth).apparent().altaz()
                
                # 只绘制两颗星都在地平线以上的连线
                if alt1.degrees > 0 and alt2.degrees > 0:
                    ax.plot([ra1, ra2], [90 - dec1, 90 - dec2], 'w-', alpha=0.3, linewidth=0.5)
    
    # 设置图形属性
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 90)
    
    # 保存图像到内存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=transparent, bbox_inches='tight', pad_inches=0)
    plt.close()
    buf.seek(0)
    
    return buf 
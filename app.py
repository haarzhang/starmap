from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
import pytz
import io
from star_map import collect_celestial_data

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取表单数据
        location = request.form.get('location', '北京')
        date = request.form.get('date')
        time = request.form.get('time')
        transparent = request.form.get('transparent') == 'true'
        
        # 组合日期和时间
        datetime_str = f"{date} {time}"
        beijing_tz = pytz.timezone('Asia/Shanghai')
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        dt = beijing_tz.localize(dt)
        
        # 生成星图
        img = collect_celestial_data(location, dt, transparent)
        
        # 保存图片到内存
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # 返回图片和文件名
        filename = f"star_map_{location}_{date}_{time.replace(':', '-')}.png"
        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )
    
    # 获取当前北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)
    
    return render_template('index.html', 
                         current_date=now.strftime('%Y-%m-%d'),
                         current_time=now.strftime('%H:%M'))

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
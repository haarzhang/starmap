from flask import Flask, render_template, request, send_file
from datetime import datetime
import pytz
import io
from star_map import collect_celestial_data

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 获取表单数据
            location = request.form.get('location', '北京')
            date = request.form.get('date')
            time = request.form.get('time')
            transparent = request.form.get('transparent') == 'true'
            
            # 组合日期和时间，并添加时区信息
            beijing_tz = pytz.timezone('Asia/Shanghai')
            when_str = f"{date} {time}:00"
            when = datetime.strptime(when_str, '%Y-%m-%d %H:%M:%S')
            when = beijing_tz.localize(when)
            
            # 生成星图
            star_map = collect_celestial_data(location, when, transparent)
            
            # 将图像保存到内存中
            img_io = io.BytesIO()
            star_map.save(img_io, 'PNG')
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/png')
            
        except Exception as e:
            return str(e), 400
    
    # GET 请求：显示表单
    beijing_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(beijing_tz)
    return render_template('index.html', 
                         current_date=current_time.strftime('%Y-%m-%d'),
                         current_time=current_time.strftime('%H:%M'))

if __name__ == '__main__':
    app.run(debug=True, port=5001) 
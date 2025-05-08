from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
import pytz
import io
import logging
from star_map import collect_celestial_data

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 获取表单数据
            location = request.form.get('location', '北京')
            date = request.form.get('date')
            time = request.form.get('time')
            transparent = request.form.get('transparent') == 'on'
            
            logger.info(f"生成星图请求: 位置={location}, 日期={date}, 时间={time}, 透明={transparent}")
            
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
            
            logger.info("星图生成成功")
            return send_file(img_io, mimetype='image/png')
            
        except Exception as e:
            logger.error(f"生成星图时出错: {str(e)}")
            return jsonify({'error': str(e)}), 400
    
    # 获取当前时间（北京时间）
    beijing_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(beijing_tz)
    
    return render_template('index.html', 
                         current_date=current_time.strftime("%Y-%m-%d"),
                         current_time=current_time.strftime("%H:%M"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 
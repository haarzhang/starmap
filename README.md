# 星图生成器

这是一个基于 Flask 的 Web 应用程序，可以根据指定的位置、日期和时间生成星图。

## 功能特点

- 支持输入任意城市名称
- 可选择具体日期和时间
- 支持透明/不透明背景
- 实时生成星图
- 显示星座连线
- 根据星等显示不同大小的恒星

## 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd starmap
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 确保以下数据文件存在于项目目录中：
- `de421.bsp`（天文历表）
- `constellationship.fab`（星座连线数据）

## 运行

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5001`

## 使用说明

1. 在输入框中输入城市名称（默认为"北京"）
2. 选择日期和时间
3. 选择是否需要透明背景
4. 点击"生成星图"按钮
5. 等待星图生成完成

## 技术栈

- Flask：Web 框架
- Skyfield：天文计算
- Matplotlib：图像生成
- Geopy：地理编码
- HTML/CSS/JavaScript：前端界面

## 注意事项

- 需要稳定的网络连接以获取地理位置信息
- 生成星图可能需要几秒钟时间
- 建议使用现代浏览器访问

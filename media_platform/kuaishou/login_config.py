# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

from dataclasses import dataclass
from typing import List


@dataclass
class LoginTimeouts:
    """登录相关超时配置"""
    login_button_selector: int = 5000  # 登录按钮选择器超时(毫秒)
    qrcode_selector: int = 30000  # 二维码选择器超时(毫秒)
    click_element: int = 30000  # 元素点击超时(毫秒)
    click_retry_interval: int = 1  # 点击重试间隔(秒)
    page_load_wait: int = 3  # 页面加载等待(秒)
    login_dialog_wait: int = 2  # 登录对话框等待(秒)
    redirect_wait: int = 5  # 登录成功后重定向等待(秒)


@dataclass
class LoginSelectors:
    """登录相关选择器配置"""
    
    # 登录按钮选择器(按优先级排序)
    login_buttons: List[str] = None
    
    # 二维码选择器(按优先级排序) 
    qrcode_images: List[str] = None
    
    def __post_init__(self):
        if self.login_buttons is None:
            self.login_buttons = [
                "xpath=//p[text()='登录']",
                "xpath=//span[text()='登录']", 
                "xpath=//div[text()='登录']",
                "xpath=//button[text()='登录']",
                "css=.login-btn",
                "css=[data-testid='login-button']",
            ]
            
        if self.qrcode_images is None:
            self.qrcode_images = [
                "//div[@class='qrcode-img']//img",
                "//img[contains(@class, 'qrcode')]",
                "//div[contains(@class, 'qr')]//img",
                "//img[contains(@src, 'qr')]",
                "css=.qrcode img",
                "css=[class*='qr'] img",
            ]


@dataclass
class LoginStrategies:
    """登录策略配置"""
    
    # 点击方法配置
    click_methods: List[dict] = None
    
    # 错误处理配置
    enable_screenshots: bool = True
    screenshot_path_template: str = "/tmp/kuaishou_{action}_{timestamp}.png"
    
    def __post_init__(self):
        if self.click_methods is None:
            self.click_methods = [
                {"name": "标准点击", "method": "standard", "force": False},
                {"name": "强制点击", "method": "standard", "force": True},
                {"name": "JavaScript点击", "method": "javascript", "force": False},
                {"name": "模拟鼠标点击", "method": "mouse", "force": False},
                {"name": "延迟后点击", "method": "delayed", "force": True},
            ]


class KuaishouLoginConfig:
    """快手登录配置管理器"""
    
    def __init__(self):
        self.timeouts = LoginTimeouts()
        self.selectors = LoginSelectors()
        self.strategies = LoginStrategies()
    
    def update_timeouts(self, **kwargs):
        """更新超时配置"""
        for key, value in kwargs.items():
            if hasattr(self.timeouts, key):
                setattr(self.timeouts, key, value)
    
    def update_selectors(self, **kwargs):
        """更新选择器配置"""
        for key, value in kwargs.items():
            if hasattr(self.selectors, key):
                setattr(self.selectors, key, value)
    
    def update_strategies(self, **kwargs):
        """更新策略配置"""
        for key, value in kwargs.items():
            if hasattr(self.strategies, key):
                setattr(self.strategies, key, value) 
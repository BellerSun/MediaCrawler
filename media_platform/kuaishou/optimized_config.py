# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

from .login_config import KuaishouLoginConfig


class OptimizedKuaishouConfig:
    """快手登录优化配置"""
    
    @staticmethod
    def create_aggressive_config() -> KuaishouLoginConfig:
        """
        激进优化配置 - 最大性能提升，节省40-50秒
        适用于网络条件良好的环境
        """
        config = KuaishouLoginConfig()
        
        # 大幅减少超时时间
        config.update_timeouts(
            login_button_selector=2000,  # 5秒 -> 2秒
            qrcode_selector=5000,        # 30秒 -> 5秒
            click_element=10000,         # 30秒 -> 10秒
            click_retry_interval=0.3,    # 1秒 -> 0.3秒
            page_load_wait=1,           # 3秒 -> 1秒
            login_dialog_wait=1,        # 2秒 -> 1秒
        )
        
        # 优化点击策略 - 优先使用强制点击
        config.update_strategies(
            click_methods=[
                {"name": "遮罩层检测+强制点击", "method": "standard", "force": True},
                {"name": "JavaScript点击", "method": "javascript", "force": False},
                {"name": "标准点击", "method": "standard", "force": False},
                {"name": "延迟后强制点击", "method": "delayed", "force": True},
            ]
        )
        
        return config
    
    @staticmethod
    def create_balanced_config() -> KuaishouLoginConfig:
        """
        平衡优化配置 - 性能和稳定性平衡，节省20-30秒
        适用于大多数环境
        """
        config = KuaishouLoginConfig()
        
        # 适度减少超时时间
        config.update_timeouts(
            login_button_selector=3000,  # 5秒 -> 3秒
            qrcode_selector=10000,       # 30秒 -> 10秒
            click_element=15000,         # 30秒 -> 15秒
            click_retry_interval=0.5,    # 1秒 -> 0.5秒
            page_load_wait=2,           # 3秒 -> 2秒
            login_dialog_wait=1.5,      # 2秒 -> 1.5秒
        )
        
        return config
    
    @staticmethod
    def create_conservative_config() -> KuaishouLoginConfig:
        """
        保守优化配置 - 最小风险，节省10-15秒
        适用于网络条件不稳定的环境
        """
        config = KuaishouLoginConfig()
        
        # 小幅减少超时时间
        config.update_timeouts(
            login_button_selector=4000,  # 5秒 -> 4秒
            qrcode_selector=15000,       # 30秒 -> 15秒
            click_element=20000,         # 30秒 -> 20秒
            click_retry_interval=0.8,    # 1秒 -> 0.8秒
            page_load_wait=2.5,         # 3秒 -> 2.5秒
            login_dialog_wait=1.8,      # 2秒 -> 1.8秒
        )
        
        # 添加遮罩层检测逻辑
        config.update_strategies(
            click_methods=[
                {"name": "标准点击", "method": "standard", "force": False},
                {"name": "遮罩层检测+强制点击", "method": "standard", "force": True},
                {"name": "JavaScript点击", "method": "javascript", "force": False},
                {"name": "模拟鼠标点击", "method": "mouse", "force": False},
                {"name": "延迟后点击", "method": "delayed", "force": True},
            ]
        )
        
        return config
    
    @staticmethod
    def create_concurrent_optimized_config() -> KuaishouLoginConfig:
        """
        并发优化配置 - 专为并发执行优化
        结合并发查找和优化的超时设置
        """
        config = KuaishouLoginConfig()
        
        # 并发模式下的优化超时设置
        config.update_timeouts(
            login_button_selector=8000,  # 并发模式下可以设置更长的总超时
            qrcode_selector=12000,       # 因为实际等待时间是最快的选择器
            click_element=12000,
            click_retry_interval=0.2,    # 更短的重试间隔
            page_load_wait=1.5,
            login_dialog_wait=1,
        )
        
        # 优化选择器顺序 - 把最常成功的放在前面
        config.update_selectors(
            login_buttons=[
                "xpath=//p[text()='登录']",           # 最常见的选择器
                "xpath=//span[text()='登录']", 
                "css=.login-btn",                    # CSS选择器通常更快
                "css=[data-testid='login-button']",
                "xpath=//div[text()='登录']",
                "xpath=//button[text()='登录']",
            ],
            qrcode_images=[
                "//div[contains(@class, 'qr')]//img",  # 最常见的二维码选择器
                "css=[class*='qr'] img",              # CSS选择器
                "//div[@class='qrcode-img']//img",
                "//img[contains(@class, 'qrcode')]",
                "//img[contains(@src, 'qr')]",
                "css=.qrcode img",
            ]
        )
        
        return config


def get_config_by_environment(env_type: str = "balanced") -> KuaishouLoginConfig:
    """
    根据环境类型获取优化配置
    
    Args:
        env_type: 环境类型
            - "aggressive": 激进优化，适用于高性能环境
            - "balanced": 平衡优化，适用于一般环境
            - "conservative": 保守优化，适用于不稳定环境  
            - "concurrent": 并发优化，适用于支持并发的环境
            
    Returns:
        对应的配置对象
    """
    config_map = {
        "aggressive": OptimizedKuaishouConfig.create_aggressive_config,
        "balanced": OptimizedKuaishouConfig.create_balanced_config,
        "conservative": OptimizedKuaishouConfig.create_conservative_config,
        "concurrent": OptimizedKuaishouConfig.create_concurrent_optimized_config,
    }
    
    if env_type not in config_map:
        print(f"⚠ 未知的环境类型 '{env_type}'，使用默认的平衡配置")
        env_type = "balanced"
    
    return config_map[env_type]()


def print_config_comparison():
    """打印各种配置的对比信息"""
    configs = {
        "默认配置": KuaishouLoginConfig(),
        "激进优化": OptimizedKuaishouConfig.create_aggressive_config(),
        "平衡优化": OptimizedKuaishouConfig.create_balanced_config(),
        "保守优化": OptimizedKuaishouConfig.create_conservative_config(),
        "并发优化": OptimizedKuaishouConfig.create_concurrent_optimized_config(),
    }
    
    print("\n📊 快手登录配置对比")
    print("=" * 80)
    print(f"{'配置类型':<12} {'按钮超时':<8} {'二维码超时':<10} {'点击超时':<8} {'重试间隔':<8} {'预期节省时间'}")
    print("-" * 80)
    
    expected_savings = {
        "默认配置": "0秒",
        "激进优化": "40-50秒", 
        "平衡优化": "20-30秒",
        "保守优化": "10-15秒",
        "并发优化": "25-35秒"
    }
    
    for name, config in configs.items():
        print(f"{name:<12} "
              f"{config.timeouts.login_button_selector/1000:.1f}秒{'':<4} "
              f"{config.timeouts.qrcode_selector/1000:.1f}秒{'':<6} "
              f"{config.timeouts.click_element/1000:.1f}秒{'':<4} "
              f"{config.timeouts.click_retry_interval:.1f}秒{'':<5} "
              f"{expected_savings[name]}")


if __name__ == "__main__":
    print_config_comparison() 
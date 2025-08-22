# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


import asyncio
import sys
from typing import Optional

import cmd_arg
import config
import db
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
from utils.browser_fix import BrowserAutoFixer


class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler,
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError(
                "Invalid Media Platform Currently only supported xhs or dy or ks or bili ..."
            )
        return crawler_class()


crawler: Optional[AbstractCrawler] = None


# auto_fix_browser_issue 功能已移到 utils.browser_fix.BrowserAutoFixer 类中


async def main():
    # Init crawler
    global crawler

    # parse cmd
    await cmd_arg.parse_cmd()

    # init db
    if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
        await db.init_db()

    crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
    await crawler.start()


async def cleanup():
    if crawler:
        await crawler.close()
    if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
        await db.close()


if __name__ == "__main__":
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            asyncio.get_event_loop().run_until_complete(main())
            break  # 成功执行，退出循环
            
        except KeyboardInterrupt:
            print("程序被用户中断")
            break
            
        except Exception as e:
            error_message = str(e)
            print(f"程序运行出错: {error_message}")
            
            # 检查是否是浏览器相关错误
            is_browser_error = BrowserAutoFixer.is_browser_error(error_message)
            
            if is_browser_error and retry_count < max_retries - 1:
                print(f"\n🤖 检测到浏览器问题（第 {retry_count + 1} 次失败），正在自动处理...")
                
                # 自动清理
                if BrowserAutoFixer.auto_fix():
                    retry_count += 1
                    print(f"\n🔄 准备重试... (尝试 {retry_count + 1}/{max_retries})")
                    print("⏳ 等待 3 秒后重新启动...")
                    
                    # 清理当前爬虫实例
                    try:
                        if crawler:
                            asyncio.get_event_loop().run_until_complete(crawler.close())
                            crawler = None
                    except:
                        pass
                    
                    # 等待一下再重试
                    import time
                    time.sleep(3)
                    continue
                else:
                    print("❌ 自动清理失败，请手动处理")
                    break
            else:
                # 非浏览器错误或重试次数已达上限
                if is_browser_error:
                    print(f"\n❌ 已重试 {max_retries} 次仍然失败")
                    print("\n📋 手动解决方案:")
                    print("1. 运行: python fix_browser_issue.py")
                    print("2. 检查系统资源（内存、磁盘空间）")
                    print("3. 重启系统后再试")
                else:
                    print("\n📋 其他错误，请检查配置和网络连接")
                break
                
        finally:
            try:
                asyncio.get_event_loop().run_until_complete(cleanup())
            except Exception as e:
                print(f"清理资源时出错: {e}")
    
    print("进程退出，退出码: -1") 
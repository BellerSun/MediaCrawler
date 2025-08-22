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
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        error_message = str(e)
        print(f"程序运行出错: {error_message}")
        
        # 提供特定错误的解决方案提示
        if "Target page, context or browser has been closed" in error_message:
            print("\n解决方案:")
            print("1. 运行: python fix_browser_issue.py")
            print("2. 或者手动清理浏览器数据目录: rm -rf browser_data/ks_user_data_dir")
            print("3. 然后重新运行程序")
        elif "browser_context" in error_message and "attribute" in error_message:
            print("\n解决方案:")
            print("1. 这可能是浏览器初始化失败导致的")
            print("2. 运行: python fix_browser_issue.py")
            print("3. 检查系统资源是否充足（内存、磁盘空间）")
    finally:
        try:
            asyncio.get_event_loop().run_until_complete(cleanup())
        except Exception as e:
            print(f"清理资源时出错: {e}")
        print("进程退出，退出码: -1")

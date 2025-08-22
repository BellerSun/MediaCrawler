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
import functools
import sys
from typing import Optional

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from tenacity import (RetryError, retry, retry_if_result, stop_after_attempt,
                      wait_fixed)

import config
from base.base_crawler import AbstractLogin
from tools import utils


class KuaishouLogin(AbstractLogin):
    def __init__(self,
                 login_type: str,
                 browser_context: BrowserContext,
                 context_page: Page,
                 login_phone: Optional[str] = "",
                 cookie_str: str = ""
                 ):
        config.LOGIN_TYPE = login_type
        self.browser_context = browser_context
        self.context_page = context_page
        self.login_phone = login_phone
        self.cookie_str = cookie_str

    async def begin(self):
        """Start login xiaohongshu"""
        utils.logger.info("[KuaishouLogin.begin] Begin login kuaishou ...")
        if config.LOGIN_TYPE == "qrcode":
            await self.login_by_qrcode()
        elif config.LOGIN_TYPE == "phone":
            await self.login_by_mobile()
        elif config.LOGIN_TYPE == "cookie":
            await self.login_by_cookies()
        else:
            raise ValueError("[KuaishouLogin.begin] Invalid Login Type Currently only supported qrcode or phone or cookie ...")

    @retry(stop=stop_after_attempt(600), wait=wait_fixed(1), retry=retry_if_result(lambda value: value is False))
    async def check_login_state(self) -> bool:
        """
            Check if the current login status is successful and return True otherwise return False
            retry decorator will retry 20 times if the return value is False, and the retry interval is 1 second
            if max retry times reached, raise RetryError
        """
        current_cookie = await self.browser_context.cookies()
        _, cookie_dict = utils.convert_cookies(current_cookie)
        kuaishou_pass_token = cookie_dict.get("passToken")
        if kuaishou_pass_token:
            return True
        return False

    async def _try_click_with_multiple_methods(self, login_button_ele):
        """尝试多种点击方法"""
        methods = [
            ("标准点击", lambda: login_button_ele.click()),
            ("强制点击", lambda: login_button_ele.click(force=True)),
            ("JavaScript点击", lambda: login_button_ele.evaluate("element => element.click()")),
            ("模拟鼠标点击", lambda: login_button_ele.click(button="left", click_count=1)),
            ("延迟后点击", lambda: self._delayed_click(login_button_ele)),
        ]
        
        for method_name, click_method in methods:
            try:
                utils.logger.info(f"[KuaishouLogin] 尝试{method_name}...")
                await click_method()
                utils.logger.info(f"[KuaishouLogin] {method_name}成功")
                return True
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] {method_name}失败: {e}")
                await asyncio.sleep(1)
        
        return False

    async def _delayed_click(self, element):
        """延迟点击方法"""
        await asyncio.sleep(2)
        await element.click(force=True)

    async def _check_page_state(self):
        """检查页面状态"""
        try:
            # 检查页面标题
            title = await self.context_page.title()
            utils.logger.info(f"[KuaishouLogin] 页面标题: {title}")
            
            # 检查页面URL
            url = self.context_page.url
            utils.logger.info(f"[KuaishouLogin] 当前URL: {url}")
            
            # 检查页面是否加载完成
            ready_state = await self.context_page.evaluate("document.readyState")
            utils.logger.info(f"[KuaishouLogin] 页面加载状态: {ready_state}")
            
            # 检查是否有遮罩层
            overlays = await self.context_page.query_selector_all("div[style*='z-index'], div[class*='mask'], div[class*='overlay']")
            utils.logger.info(f"[KuaishouLogin] 发现可能的遮罩层数量: {len(overlays)}")
            
            return True
        except Exception as e:
            utils.logger.error(f"[KuaishouLogin] 检查页面状态失败: {e}")
            return False

    async def _wait_for_login_button(self):
        """等待登录按钮可用"""
        selectors = [
            "xpath=//p[text()='登录']",
            "xpath=//span[text()='登录']",
            "xpath=//div[text()='登录']",
            "xpath=//button[text()='登录']",
            "css=.login-btn",
            "css=[data-testid='login-button']",
        ]
        
        for i, selector in enumerate(selectors):
            try:
                utils.logger.info(f"[KuaishouLogin] 尝试选择器 {i+1}/{len(selectors)}: {selector}")
                element = await self.context_page.wait_for_selector(selector, timeout=5000)
                if element:
                    # 检查元素状态
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    utils.logger.info(f"[KuaishouLogin] 元素状态 - 可见: {is_visible}, 可用: {is_enabled}")
                    
                    if is_visible and is_enabled:
                        return element
                        
            except PlaywrightTimeoutError:
                utils.logger.warning(f"[KuaishouLogin] 选择器 {selector} 超时")
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] 选择器 {selector} 出错: {e}")
        
        return None

    async def login_by_qrcode(self):
        """login kuaishou website and keep webdriver login state"""
        utils.logger.info("[KuaishouLogin.login_by_qrcode] Begin login kuaishou by qrcode ...")
        
        # 检查页面状态
        await self._check_page_state()
        
        # 等待页面完全加载
        await asyncio.sleep(3)
        utils.logger.info("[KuaishouLogin] 等待页面加载完成...")
        
        # 尝试等待并找到登录按钮
        login_button_ele = await self._wait_for_login_button()
        
        if not login_button_ele:
            # 尝试原始选择器作为最后的备选
            utils.logger.warning("[KuaishouLogin] 使用原始选择器作为备选...")
            login_button_ele = self.context_page.locator("xpath=//p[text()='登录']")

        # 尝试多种点击方法
        utils.logger.info("[KuaishouLogin] 开始尝试点击登录按钮...")
        click_success = await self._try_click_with_multiple_methods(login_button_ele)
        
        if not click_success:
            utils.logger.error("[KuaishouLogin] 所有点击方法都失败了")
            
            # 尝试截图以便调试
            try:
                screenshot_path = "/tmp/kuaishou_login_failed.png"
                await self.context_page.screenshot(path=screenshot_path)
                utils.logger.info(f"[KuaishouLogin] 已保存截图到: {screenshot_path}")
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] 截图失败: {e}")
            
            # 最后尝试：直接执行JavaScript
            try:
                utils.logger.info("[KuaishouLogin] 最后尝试：直接JavaScript点击...")
                await self.context_page.evaluate("""
                    const buttons = Array.from(document.querySelectorAll('p, span, div, button'));
                    const loginBtn = buttons.find(btn => btn.textContent && btn.textContent.includes('登录'));
                    if (loginBtn) {
                        loginBtn.click();
                        console.log('JavaScript点击成功');
                    } else {
                        console.log('未找到登录按钮');
                    }
                """)
                utils.logger.info("[KuaishouLogin] JavaScript点击执行完成")
            except Exception as e:
                utils.logger.error(f"[KuaishouLogin] JavaScript点击也失败了: {e}")
                
        # 等待登录弹窗出现
        await asyncio.sleep(2)
        
        # 再次检查页面状态
        await self._check_page_state()

        # find login qrcode
        utils.logger.info("[KuaishouLogin] 开始查找二维码...")
        qrcode_selectors = [
            "//div[@class='qrcode-img']//img",
            "//img[contains(@class, 'qrcode')]",
            "//div[contains(@class, 'qr')]//img",
            "//img[contains(@src, 'qr')]",
            "css=.qrcode img",
            "css=[class*='qr'] img",
        ]
        
        base64_qrcode_img = None
        for i, selector in enumerate(qrcode_selectors):
            try:
                utils.logger.info(f"[KuaishouLogin] 尝试二维码选择器 {i+1}/{len(qrcode_selectors)}: {selector}")
                base64_qrcode_img = await utils.find_login_qrcode(
                    self.context_page,
                    selector=selector
                )
                if base64_qrcode_img:
                    utils.logger.info(f"[KuaishouLogin] 成功找到二维码，使用选择器: {selector}")
                    break
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] 二维码选择器 {selector} 失败: {e}")
        
        if not base64_qrcode_img:
            utils.logger.error("[KuaishouLogin] login failed , have not found qrcode please check ....")
            
            # 尝试截图
            try:
                screenshot_path = "/tmp/kuaishou_no_qrcode.png"
                await self.context_page.screenshot(path=screenshot_path)
                utils.logger.info(f"[KuaishouLogin] 已保存无二维码截图到: {screenshot_path}")
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] 截图失败: {e}")
                
            # 打印页面内容用于调试
            try:
                page_content = await self.context_page.content()
                utils.logger.debug(f"[KuaishouLogin] 页面内容长度: {len(page_content)}")
                # 查找可能的二维码相关元素
                qr_elements = await self.context_page.query_selector_all("*[class*='qr'], *[class*='code'], img")
                utils.logger.info(f"[KuaishouLogin] 找到可能相关的元素数量: {len(qr_elements)}")
            except Exception as e:
                utils.logger.warning(f"[KuaishouLogin] 获取页面内容失败: {e}")
                
            sys.exit()

        # show login qrcode
        utils.logger.info("[KuaishouLogin] 显示二维码...")
        partial_show_qrcode = functools.partial(utils.show_qrcode, base64_qrcode_img)
        asyncio.get_running_loop().run_in_executor(executor=None, func=partial_show_qrcode)

        utils.logger.info(f"[KuaishouLogin.login_by_qrcode] waiting for scan code login, remaining time is 20s")
        try:
            await self.check_login_state()
        except RetryError:
            utils.logger.info("[KuaishouLogin.login_by_qrcode] Login kuaishou failed by qrcode login method ...")
            sys.exit()

        wait_redirect_seconds = 5
        utils.logger.info(f"[KuaishouLogin.login_by_qrcode] Login successful then wait for {wait_redirect_seconds} seconds redirect ...")
        await asyncio.sleep(wait_redirect_seconds)

    async def login_by_mobile(self):
        pass

    async def login_by_cookies(self):
        utils.logger.info("[KuaishouLogin.login_by_cookies] Begin login kuaishou by cookie ...")
        for key, value in utils.convert_str_cookie_to_dict(self.cookie_str).items():
            await self.browser_context.add_cookies([{
                'name': key,
                'value': value,
                'domain': ".kuaishou.com",
                'path': "/"
            }])

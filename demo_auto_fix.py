#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动浏览器修复功能演示脚本
展示当遇到浏览器错误时如何自动处理
"""

import asyncio
from utils.browser_fix import BrowserAutoFixer


async def simulate_browser_error():
    """模拟浏览器启动错误的情况"""
    print("🎯 模拟浏览器启动错误场景...")
    
    # 模拟不同类型的浏览器错误
    browser_errors = [
        "Target page, context or browser has been closed",
        "BrowserType.launch_persistent_context: Target page has been closed",
        "browser_context attribute error",
        "Connection closed before receiving a handshake response"
    ]
    
    print("📋 支持自动检测的浏览器错误类型:")
    for i, error in enumerate(browser_errors, 1):
        is_detected = BrowserAutoFixer.is_browser_error(error)
        status = "✅ 可检测" if is_detected else "❌ 不可检测"
        print(f"  {i}. {error} - {status}")
    
    print("\n" + "="*60)


async def demo_auto_fix():
    """演示自动修复功能"""
    print("🔧 自动修复功能演示")
    print("="*60)
    
    # 执行清理
    result = BrowserAutoFixer.auto_fix()
    
    if result:
        print("✅ 演示完成：自动修复功能正常工作")
    else:
        print("⚠ 演示结果：自动修复过程中遇到一些问题，但这是正常的")
    
    return result


async def demo_retry_mechanism():
    """演示带重试的自动修复机制"""
    print("\n🔄 自动重试机制演示")
    print("="*60)
    
    async def failing_function():
        """模拟会失败的浏览器启动函数"""
        raise Exception("Target page, context or browser has been closed")
    
    print("📝 演示场景：模拟浏览器启动失败，然后自动清理和重试")
    print("💡 注意：这只是演示，实际会执行真正的清理操作")
    
    try:
        # 使用自动修复重试机制
        success = await BrowserAutoFixer.auto_fix_with_retry(failing_function, max_retries=1)
        if success:
            print("✅ 重试成功")
        else:
            print("❌ 重试失败（这是预期的，因为我们故意让函数失败）")
    except Exception as e:
        print(f"🎯 捕获到预期的错误: {e}")
        print("✅ 重试机制演示完成")


def show_features():
    """展示新功能特点"""
    print("\n🎉 新增的自动修复功能特点:")
    print("="*60)
    
    features = [
        "🤖 智能错误检测：自动识别浏览器相关错误",
        "🔧 自动清理：无需手动运行修复脚本",
        "🔄 自动重试：清理后自动重试，减少用户操作",
        "📊 详细统计：显示清理过程和结果统计",
        "🎯 精准清理：只清理相关进程和文件，避免误删",
        "🚀 快速恢复：通常只需3-5秒即可完成清理",
        "📋 友好提示：提供清晰的状态反馈和建议",
        "🔍 多场景支持：支持快手、抖音等多个平台的浏览器问题"
    ]
    
    for feature in features:
        print(f"  • {feature}")


async def main():
    """主演示函数"""
    print("🚀 MediaCrawler 自动浏览器修复功能演示")
    print("="*60)
    print("⚠ 重要说明：此脚本会执行真正的浏览器进程清理操作")
    print("如果您不希望清理浏览器进程，请按 Ctrl+C 退出")
    
    # 等待用户确认
    try:
        input("\n按 Enter 键继续演示，或按 Ctrl+C 退出...")
    except KeyboardInterrupt:
        print("\n👋 演示已取消")
        return
    
    # 1. 模拟错误检测
    await simulate_browser_error()
    
    # 2. 演示自动修复
    await demo_auto_fix()
    
    # 3. 演示重试机制
    await demo_retry_mechanism()
    
    # 4. 展示功能特点
    show_features()
    
    print("\n" + "="*60)
    print("🎊 演示完成！")
    print("\n💡 使用建议:")
    print("  现在当您运行爬虫遇到浏览器错误时，")
    print("  程序会自动尝试清理和重试，无需手动干预！")
    print("\n📖 更多信息:")
    print("  • 主程序已集成自动重试功能（最多3次）")
    print("  • 快手爬虫启动失败时会自动尝试清理")
    print("  • 仍可手动运行 'python fix_browser_issue.py' 进行清理")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 演示已中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        print("这可能是正常的，因为我们在演示错误处理功能") 
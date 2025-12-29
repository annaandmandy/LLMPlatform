"""
Test script to verify Phase 3 implementation (Providers).

Run this to test:
    python -m app.scripts.test_phase3
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def main():
    print("=" * 60)
    print("🧪 Testing Phase 3: LLM Providers")
    print("=" * 60)
    
    # Test 1: Base Provider Interface
    print("\n📋 Test 1: Base Provider Interface")
    try:
        from app.providers.base import BaseLLMProvider
        print("✅ BaseLLMProvider imported")
        
        # Check abstract methods
        assert hasattr(BaseLLMProvider, 'generate')
        assert hasattr(BaseLLMProvider, 'supports_streaming')
        assert hasattr(BaseLLMProvider, 'supports_vision')
        print("✅ Abstract methods defined")
        
        print("✅ Base provider test PASSED")
    except Exception as e:
        print(f"❌ Base provider test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Provider Implementations
    print("\n🔌 Test 2: Provider Implementations")
    try:
        from app.providers import (
            OpenAIProvider,
            AnthropicProvider,
            GoogleProvider,
            OpenRouterProvider
        )
        
        print("✅ OpenAIProvider imported")
        print("✅ AnthropicProvider imported")
        print("✅ GoogleProvider imported")
        print("✅ OpenRouterProvider imported")
        
        # Test instantiation (without API keys - should work)
        try:
            openai  = OpenAIProvider()
            print(f"✅ OpenAIProvider instantiated: {openai.provider_name}")
        except ValueError as e:
            if "not configured" in str(e):
                print(f"⚠️  OpenAIProvider not configured (expected if no API key)")
            else:
                raise
        
        print("✅ Provider implementations test PASSED")
    except Exception as e:
        print(f"❌ Provider implementations test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Provider Factory
    print("\n🏭 Test 3: Provider Factory")
    try:
        from app.providers.factory import ProviderFactory
        
        # List providers
        providers = ProviderFactory.list_providers()
        print(f"✅ Registered providers: {providers}")
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "openrouter" in providers
        
        # Test getting provider (without API key will fail,  but that's OK)
        try:
            provider = ProviderFactory.get_provider("openai")
            print(f"✅ Got provider: {provider.provider_name}")
        except ValueError as e:
            if "not configured" in str(e):
                print(f"⚠️  Provider not configured (expected if no API key)")
            else:
                raise
        
        # Test legacy compatibility wrapper
        llm_functions = ProviderFactory.get_all_providers()
        print(f"✅ Legacy functions created: {list(llm_functions.keys())}")
        assert "openai" in llm_functions
        assert "anthropic" in llm_functions
        
        print("✅ Provider factory test PASSED")
    except Exception as e:
        print(f"❌ Provider factory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Provider Capabilities
    print("\n⚡ Test 4: Provider Capabilities")
    try:
        from app.providers import (
            OpenAIProvider,
            AnthropicProvider,
            GoogleProvider,
            OpenRouterProvider
        )
        
        # Test with dummy API keys to check methods
        openai_p = OpenAIProvider(api_key="test_key")
        anthropic_p = AnthropicProvider(api_key="test_key")
        google_p = GoogleProvider(api_key="test_key")
        openrouter_p = OpenRouterProvider(api_key="test_key")
        
        # Test capabilities
        print(f"✅ OpenAI streaming: {openai_p.supports_streaming()}")
        print(f"✅ OpenAI vision (gpt-4o): {openai_p.supports_vision('gpt-4o')}")
        print(f"✅ OpenAI web search (search-preview): {openai_p.supports_web_search('gpt-4o-search-preview')}")
        
        print(f"✅ Anthropic streaming: {anthropic_p.supports_streaming ()}")
        print(f"✅ Anthropic vision (claude-3): {anthropic_p.supports_vision('claude-3-opus')}")
        print(f"✅ Anthropic web search: {anthropic_p.supports_web_search('claude-3')}")
        
        print(f"✅ Google streaming: {google_p.supports_streaming()}")
        print(f"✅ Google vision (gemini-2): {google_p.supports_vision('gemini-2.0')}")
        print(f"✅ Google web search: {google_p.supports_web_search('gemini-pro')}")
        
        print(f"✅ OpenRouter streaming: {openrouter_p.supports_streaming()}")
        print(f"✅ OpenRouter web search (perplexity): {openrouter_p.supports_web_search('perplexity-online')}")
        
        print("✅ Provider capabilities test PASSED")
    except Exception as e:
        print(f"❌ Provider capabilities test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Agent Integration
    print("\n🤖 Test 5: Agent Integration")
    try:
        from app.agents import _get_llm_functions
        
        llm_functions = _get_llm_functions()
        print(f"✅ Agent LLM functions loaded: {list(llm_functions.keys())}")
        
        # Check if they're callable
        for name, fn in llm_functions.items():
            assert callable(fn), f"{name} is not callable"
        print("✅ All functions are callable")
        
        print("✅ Agent integration test PASSED")
    except Exception as e:
        print(f"❌ Agent integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Package Import
    print("\n📦 Test 6: Package-level Import")
    try:
        from app.providers import (
            BaseLLMProvider,
            OpenAIProvider,
            AnthropicProvider,
            GoogleProvider,
            OpenRouterProvider,
            ProviderFactory
        )
        print("✅ All providers importable from app.providers")
        print("✅ Package import test PASSED")
    except Exception as e:
        print(f"❌ Package import test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✨ ALL TESTS PASSED! Phase 3 is working correctly! ✨")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
STEP 1: Simple diagnostic to identify the issue
Save this as 'diagnostic_step1.py' and run it
"""

print("🔍 STEP 1: LAM System Diagnostic")
print("=" * 40)

def test_basic_imports():
    """Test if your modules can be imported"""
    print("\n1. Testing Module Imports:")
    
    # Test enhanced_lam_integration
    try:
        import enhanced_lam_integration
        print("   ✅ enhanced_lam_integration imported")
        
        # Test specific class
        from enhanced_lam_integration import EnhancedTrueLAMInterface
        print("   ✅ EnhancedTrueLAMInterface imported")
        
    except Exception as e:
        print(f"   ❌ Enhanced LAM failed: {e}")
        return False
    
    # Test autonomous_manager  
    try:
        import autonomous_manager
        print("   ✅ autonomous_manager imported")
        
        from autonomous_manager import AutonomousProjectManager
        print("   ✅ AutonomousProjectManager imported")
        
    except Exception as e:
        print(f"   ❌ Autonomous Manager failed: {e}")
        return False
    
    return True

def test_lam_initialization():
    """Test if LAM interface initializes properly"""
    print("\n2. Testing LAM Initialization:")
    
    try:
        from enhanced_lam_integration import EnhancedTrueLAMInterface
        
        print("   🔄 Creating LAM interface...")
        lam = EnhancedTrueLAMInterface()
        
        # Check if model loaded
        if hasattr(lam, 'model') and lam.model is not None:
            print("   ✅ AI Model loaded successfully!")
            print(f"   📊 Model name: {lam.model_name}")
            return "AI_MODEL"
        else:
            print("   ⚠️  AI Model NOT loaded - using fallback mode")
            return "FALLBACK"
            
    except Exception as e:
        print(f"   ❌ LAM initialization failed: {e}")
        return "FAILED"

def test_simple_query():
    """Test a simple query to see what happens"""
    print("\n3. Testing Simple Query:")
    
    try:
        from enhanced_lam_integration import EnhancedTrueLAMInterface
        
        lam = EnhancedTrueLAMInterface()
        
        # Test the exact query you're using
        query = "Execute autonomous project management workflow"
        print(f"   🔄 Testing query: '{query}'")
        
        result = lam.process_query(query)
        
        if result.get("success"):
            response = result.get("data", "")
            print(f"   ✅ Query succeeded")
            print(f"   📊 Response length: {len(response)} characters")
            
            # Check for generic response indicators
            if "Autonomous Execution Completed" in response:
                print("   🎯 ISSUE FOUND: Generic template response detected!")
                return "GENERIC_TEMPLATE"
            elif "Multi-step autonomous reasoning applied" in response:
                print("   🎯 ISSUE FOUND: Using template, not real processing!")
                return "TEMPLATE_MODE"
            else:
                print("   ✅ Seems to be real processing")
                return "REAL_PROCESSING"
        else:
            print(f"   ❌ Query failed: {result.get('error')}")
            return "QUERY_FAILED"
            
    except Exception as e:
        print(f"   ❌ Query test failed: {e}")
        return "TEST_FAILED"

def main():
    """Run the diagnostic"""
    print("Starting diagnostic...\n")
    
    # Step 1: Test imports
    imports_ok = test_basic_imports()
    if not imports_ok:
        print("\n❌ RESULT: Module import issues - fix imports first")
        return
    
    # Step 2: Test LAM initialization  
    lam_status = test_lam_initialization()
    
    # Step 3: Test query processing
    query_status = test_simple_query()
    
    # Give diagnosis
    print("\n" + "=" * 40)
    print("🏁 DIAGNOSTIC RESULT:")
    
    if lam_status == "AI_MODEL" and query_status == "REAL_PROCESSING":
        print("✅ System working correctly with AI model")
    elif lam_status == "FALLBACK" and query_status in ["GENERIC_TEMPLATE", "TEMPLATE_MODE"]:
        print("🎯 ISSUE IDENTIFIED: Using fallback templates instead of real processing")
        print("   CAUSE: AI model not loading, falling back to pattern matching")
        print("   NEXT STEP: Fix AI model loading")
    elif query_status in ["GENERIC_TEMPLATE", "TEMPLATE_MODE"]:
        print("🎯 ISSUE IDENTIFIED: Template responses even with AI model")
        print("   CAUSE: Logic routing to templates instead of real functions") 
        print("   NEXT STEP: Fix query processing logic")
    else:
        print("❓ Unclear issue - need more investigation")
    
    print(f"\nLAM Status: {lam_status}")
    print(f"Query Status: {query_status}")

if __name__ == "__main__":
    main()
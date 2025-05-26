"""
Simple import test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.utils.fpl_data import get_players_by_form
    print("✅ Import successful")
    
    # Test async function
    import asyncio
    
    async def test():
        try:
            players = await get_players_by_form(limit=1)
            print(f"✅ Got {len(players)} players")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    result = asyncio.run(test())
    if result:
        print("✅ Basic test passed!")
    else:
        print("❌ Basic test failed!")
        
except Exception as e:
    print(f"❌ Import error: {e}")

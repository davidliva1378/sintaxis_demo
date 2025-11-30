from unittest.mock import Mock, AsyncMock, MagicMock
import asyncio

async def test():
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.error = None
    
    mock_use_case = Mock()
    mock_use_case.execute = AsyncMock(return_value=mock_result)
    
    result = await mock_use_case.execute()
    print(f"Result type: {type(result)}")
    print(f"Result success: {result.success}")
    try:
        print(f"Result error: {result.error}")
    except AttributeError as e:
        print(f"AttributeError: {e}")

if __name__ == "__main__":
    asyncio.run(test())

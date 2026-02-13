import asyncio
import logging
from application.services.patent_advisory_service import PatentAdvisoryService

logging.basicConfig(level=logging.ERROR)

async def main():
    service = PatentAdvisoryService()
    try:
        print("Invoking get_advisory for 482020668...")
        result = await service.get_advisory(482020668)
        print("Success:", result)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

from app.utils.db_logger import save_chat_request

@router.api_route("/", methods=["GET", "POST"])
async def threads(request: Request):
    if request.method == "POST":
        try:
            body = await request.json()
            save_chat_request(
                role="user",
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (threads POST):", ex)
    return await forward_openai(request, "/v1/threads")

@router.api_route("/{thread_id}", methods=["GET", "POST"])
async def thread_by_id(request: Request, thread_id: str):
    if request.method == "POST":
        try:
            body = await request.json()
            save_chat_request(
                role="user",
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (threads/{thread_id} POST):", ex)
    return await forward_openai(request, f"/v1/threads/{thread_id}")

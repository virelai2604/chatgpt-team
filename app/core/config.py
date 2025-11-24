async def _realtime_ws_roundtrip(ws_url: str, client_secret: Optional[str]) -> bool:
    if websockets is None:
        log("websockets not installed; skipping realtime WS test.")
        return False

    headers: Dict[str, str] = {}
    if client_secret:
        headers["Authorization"] = f"Bearer {client_secret}"

    debug(f"Connecting WS to {ws_url} with headers={headers!r}")

    try:
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            event = {
                "type": "input_text",
                "content": "Say exactly: relay-ws-ok",
            }
            await ws.send(json.dumps(event))

            chunks: list[str] = []
            for _ in range(100):
                msg = await ws.recv()
                debug(f"WS recv: {msg!r}")
                try:
                    obj = json.loads(msg)
                except Exception:
                    continue

                if obj.get("type") == "response.output_text.delta":
                    delta = obj.get("delta") or ""
                    if isinstance(delta, str):
                        chunks.append(delta)
                if obj.get("type") in ("response.completed", "response.completed.success"):
                    break

            text = "".join(chunks)
            log(f"Realtime WS aggregated text: {text!r}")
            return "relay-ws-ok" in text
    except Exception as exc:
        log(f"ERROR during realtime WS: {exc}")
        return False

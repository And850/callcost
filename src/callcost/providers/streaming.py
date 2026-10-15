"""Shared HTTP/SSE measurement, retaining the exact body bytes received."""

import codecs
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from callcost.records import CallResult


class SSEDecoder:
    def __init__(self):
        self.decoder = codecs.getincrementaldecoder('utf-8')()
        self.pending = ''
        self.data = []

    def feed(self, chunk: bytes, final=False):
        self.pending += self.decoder.decode(chunk, final=final)
        lines = self.pending.split('\n')
        self.pending = lines.pop()
        if final and self.pending:
            lines.append(self.pending)
            self.pending = ''
        for line in lines:
            line = line.removesuffix('\r')
            if not line:
                if self.data:
                    yield '\n'.join(self.data)
                    self.data.clear()
            elif line.startswith('data:'):
                self.data.append(line[5:].removeprefix(' '))
        if final and self.data:
            yield '\n'.join(self.data)
            self.data.clear()


def stream_request(client: httpx.Client, url: str, payload: dict, headers: dict,
                   raw_directory: Path, call_id: str, consume, *, timeout: float,
                   clock=time.perf_counter) -> CallResult:
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    (raw_directory / f'{call_id}.request.json').write_bytes(body)
    result = CallResult(request_payload_bytes=len(body))
    request_headers = {'Content-Type': 'application/json', 'Accept': 'text/event-stream',
                       'Accept-Encoding': 'identity', **headers}
    decoder = SSEDecoder()
    result.started_at = datetime.now(timezone.utc).isoformat()
    result.started_monotonic = clock()
    try:
        with (raw_directory / f'{call_id}.response.bin').open('wb') as raw:
            with client.stream('POST', url, content=body, headers=request_headers, timeout=timeout) as response:
                encoding = response.headers.get('content-encoding', 'identity')
                if encoding != 'identity':
                    raise ValueError('Compressed response despite identity request; byte interpretation unsupported')
                success = response.is_success
                for chunk in response.iter_raw():
                    now = clock()
                    if now - result.started_monotonic > timeout:
                        raise TimeoutError('Total call deadline exceeded')
                    result.response_payload_bytes += len(chunk)
                    raw.write(chunk)
                    if success:
                        for data in decoder.feed(chunk):
                            if data != '[DONE]':
                                consume(json.loads(data), now, result)
                if not success:
                    result.error = f'HTTP {response.status_code}; response body retained'
                else:
                    for data in decoder.feed(b'', final=True):
                        if data != '[DONE]':
                            consume(json.loads(data), clock(), result)
    except KeyboardInterrupt:
        result.error = 'Interrupted by user'
        result.status = 'error'
    except (httpx.HTTPError, ValueError, KeyError, TypeError, TimeoutError) as error:
        # Do not put request headers, credentials or provider error text into logs.
        result.error = f'{type(error).__name__}: request or stream failed; inspect retained response'
        result.status = 'error'
    finally:
        result.ended_monotonic = clock()
        result.latency_s = result.ended_monotonic - result.started_monotonic
    if result.status != 'completed' or result.error:
        result.status = 'error'
        result.error = result.error or 'Stream ended without a completion event'
    if result.ttft_s is None:
        result.missing['ttft_s'] = 'No answer-text event observed'
    return result


def append_answer(text, now, result):
    if not isinstance(text, str):
        raise ValueError('Answer fragment is not text')
    if text:
        if result.ttft_s is None:
            result.ttft_s = now - result.started_monotonic
        result.answer += text

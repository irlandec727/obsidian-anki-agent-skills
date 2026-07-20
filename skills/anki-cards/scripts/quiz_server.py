#!/usr/bin/env python3
"""Локальный сервер квиз-петли anki-cards.

Отдаёт HTML квиза, принимает POST /result с JSON проваленных вопросов,
пишет его в файл результата и завершается.

Запуск:
    python3 quiz_server.py [--quiz /tmp/anki_quiz.html] [--out /tmp/anki_quiz_result.json]
"""
import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="Сервер квиза anki-cards")
    p.add_argument("--quiz", default="/tmp/anki_quiz.html", help="путь к HTML квиза")
    p.add_argument("--out", default="/tmp/anki_quiz_result.json", help="куда писать результат")
    args = p.parse_args()

    html = Path(args.quiz).read_bytes()
    out_path = Path(args.out)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)

        def do_POST(self):
            if self.path != "/result":
                self.send_response(404)
                self.end_headers()
                return
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                json.loads(body)
            except ValueError:
                self.send_response(400)
                self.end_headers()
                return
            out_path.write_bytes(body)
            self.send_response(200)
            self.end_headers()
            print(f"Результат сохранён: {out_path}", flush=True)
            # shutdown() из потока обработчика — deadlock, поэтому отдельный поток
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *args):
            pass  # не засоряем вывод access-логом

    server = HTTPServer(("127.0.0.1", 0), Handler)  # порт 0 — всегда свободный
    url = f"http://localhost:{server.server_port}/"
    print(f"Квиз: {url}", flush=True)
    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()

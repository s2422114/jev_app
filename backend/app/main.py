"""FastAPI 本体。

- API キーはこちら側だけで扱う。フロントには出さない。
- Jev のクライアントは lifespan で作る。モジュール直下で作ると、
  イベントループが無い時点のループに結びついて壊れるため。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from typesafe_sdk import AsyncTypeSafeClient, TypeSafeError

from app.judge import ask_jev, evaluate
from app.material import MATERIAL
from app.models import JudgeResult

# リポジトリ直下の .env から TYPESAFE_API_KEY を環境変数に入れる。
# SDK は環境変数しか見ない（.env は自動では読まれない）。
# Render では環境変数を直接設定するので、.env が無くてもここは素通りする。
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時にクライアントを作り、終了時に閉じる。"""
    async with AsyncTypeSafeClient() as client:
        app.state.jev = client
        yield


app = FastAPI(title="jev-backend", lifespan=lifespan)


@app.get("/api/judge", response_model=JudgeResult)
async def judge(request: Request) -> JudgeResult:
    """ハードコードした材料1件を判断して返す。"""
    try:
        answers = await ask_jev(request.app.state.jev, MATERIAL)
    except TypeSafeError as error:
        # Jev の呼び出しが失敗した場合。500（backend 自身のバグ）と区別するため 502 を返す。
        # 種類（認証エラー・接続エラー・タイムアウトなど）が分かるようにクラス名を載せる。
        # 本文はそのままフロントの画面に出るので、キーなどを書かないこと。
        raise HTTPException(
            status_code=502,
            detail=f"Jev の呼び出しに失敗しました（{type(error).__name__}）: {error}",
        ) from error
    return evaluate(answers, MATERIAL)

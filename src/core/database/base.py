# src/core/database/base.py
from typing import Any

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(AsyncAttrs, DeclarativeBase):
    """모든 모델의 최상위 부모 클래스"""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # 클래스명(PascalCase)을 snake_case 테이블명으로 자동 변환
        # 예: UserProfile -> user_profile
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in cls.__name__]
        ).lstrip("_")

    # 공통 메서드 (Dict 변환 등) 추가 가능
    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from config_reader import config

engine = create_async_engine(config.database_url.get_secret_value(), echo=False)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(nullable=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_moderator: Mapped[bool] = mapped_column(default=False)
    balance: Mapped[int]

    adverts = relationship("Advert", back_populates="user")
    questions = relationship('Question', back_populates='user')


class Chat(Base):
    __tablename__ = "chats"
    id = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str]
    username: Mapped[str] = mapped_column(nullable=True)
    type: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    adverts = relationship('Advert', back_populates='chat')
    tariffs = relationship('Tariff', cascade="all,delete", back_populates='chat')


class Tariff(Base):
    __tablename__ = "tariffs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    days: Mapped[int]
    price: Mapped[int]
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('chats.id', ondelete="CASCADE"))

    adverts = relationship('Advert', back_populates='tariff')
    chat = relationship('Chat', back_populates='tariffs')


class Advert(Base):
    __tablename__ = "adverts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    chat_id: Mapped[Chat] = mapped_column(ForeignKey("chats.id", ondelete="SET NULL"), nullable=True)
    tariff_id: Mapped[Tariff] = mapped_column(ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    media_id: Mapped[str]
    media_type: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default='moderating')
    posted_at: Mapped[datetime]
    posted_message_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime]
    note: Mapped[str] = mapped_column(nullable=True)

    user = relationship("User", back_populates="adverts")
    chat = relationship('Chat', back_populates='adverts')
    tariff = relationship('Tariff', back_populates='adverts')


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[User] = mapped_column(ForeignKey("users.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="open")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow())
    answered_at: Mapped[datetime] = mapped_column(nullable=True)

    user = relationship('User', back_populates='questions')

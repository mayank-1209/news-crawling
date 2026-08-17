from sqlalchemy import Boolean, ForeignKey, Text, create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv(".env.local")
load_dotenv(".env")


LOCAL_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

SERVER_DATABASE_URL = os.getenv("SERVER_DATABASE_URL")
print("LOCAL_DATABASE_URL:", LOCAL_DATABASE_URL)
print("SERVER_DATABASE_URL:", SERVER_DATABASE_URL)

if LOCAL_DATABASE_URL:
    engine = create_engine(LOCAL_DATABASE_URL)
else:
    engine = create_engine(SERVER_DATABASE_URL)

with engine.connect() as conn:
    print("Connected successfully!")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# class SitemapURL(Base):
#     __tablename__ = "sitemap_urls"

#     id = Column(Integer, primary_key=True, index=True)
#     source_website = Column(String(255), index=True)
#     url = Column(String(2048), unique=True, index=True)
#     discovered_at = Column(DateTime, default=datetime.utcnow)
#     is_scraped = Column(Boolean, default=False)


# class NewsArticle(Base):
#     __tablename__ = "news_articles"

#     id = Column(Integer, primary_key=True, index=True)
#     url_id = Column(Integer, ForeignKey("sitemap_urls.id"), unique=True)
#     title = Column(String(500))
#     content = Column(Text)
#     image = Column(Text)
#     sitemap = relationship("SitemapURL")



class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)          
    base_url = Column(String(255), unique=True, index=True) 
    is_active = Column(Boolean, default=True)

    urls = relationship("ScrapedURL", back_populates="domain", cascade="all, delete-orphan")


# 2. Scraped URLs Table 
class ScrapedURL(Base):
    __tablename__ = "scraped_urls"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_scraped = Column(Boolean, default=False)

    domain = relationship("Domain", back_populates="urls")
    content = relationship("Content", back_populates="source_url", uselist=False)


# 3. Language Table 
class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)         
    code = Column(String(10), unique=True, index=True) 
    status = Column(Boolean, default=True)            

    content_links = relationship("ContentLanguage", back_populates="language")


# 4. Content Table 
class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("scraped_urls.id"), unique=True, index=True)
    title = Column(String(500))
    body_description = Column(Text)
    body_text = Column(Text)
    rephrased_text = Column(Text, nullable=True) 
    is_rephrased = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_url = relationship("ScrapedURL", back_populates="content")
    media = relationship("Media", back_populates="content", cascade="all, delete-orphan")
    languages = relationship("ContentLanguage", back_populates="content", cascade="all, delete-orphan")


# 5. Content-Language Mapping Table
class ContentLanguage(Base):
    __tablename__ = "content_languages"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), index=True, nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), index=True, nullable=False)

    content = relationship("Content", back_populates="languages")
    language = relationship("Language", back_populates="content_links")


# 6. Media Table 
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), index=True, nullable=False)
    media_url = Column(String(2048), nullable=False)
    base_url = Column(String(2048), nullable=True) 
    
    content = relationship("Content", back_populates="media")


    
# Create the tables in the database
Base.metadata.create_all(bind=engine)
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from typing import List, Optional
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from db_files.clothes_db import get_user_clothing_with_attributes
from flask import session

import json
import os
import playsound
import asyncio
import edge_tts
import uuid

load_dotenv(override=True)
chat_bp = Blueprint("chat", __name__, url_prefix="/api/voice")

# 출력 스키마 정의
class FashionRecommendation(BaseModel):
    키워드: List[str] = Field(description="패션 관련 핵심 키워드 5-6개")
    스타일: List[str] = Field(description="스타일 키워드 3-5개")
    추천문구: str = Field(description="자연스러운 추천 문장")


class FashionAssistant:
    def __init__(self, persist_directory: str = "./fashion_chroma_db"):
        """패션 어시스턴트 초기화"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
            max_tokens=300,
            api_key=self.api_key
        )
        
        # 임베딩 초기화
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=self.api_key
        )
        
        # ChromaDB 초기화
        self.persist_directory = persist_directory
        self.vectorstore = Chroma(
            collection_name="fashion_recommendations",
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        # JSON 파서 초기화
        self.parser = JsonOutputParser(pydantic_object=FashionRecommendation)
        
        # Few-shot 예제
        self.examples = [
            {
                "input": "비 오는 날 데이트룩 추천",
                "output": '''{
                    "키워드": ["비", "데이트", "트렌치 코트", "블라우스", "미디 스커트", "앵클부츠"],
                    "스타일": ["로맨틱", "모던", "시크"],
                    "추천문구": "비 오는 날에는 트렌치 코트와 미디 스커트로 세련되게 연출해 보세요."
                }'''
            },
            {
                "input": "겨울 회사 회식인데 깔끔하게",
                "output": '''{
                    "키워드": ["겨울", "회사 회식", "니트", "슬랙스", "체스터 코트", "더비슈즈"],
                    "스타일": ["클래식", "미니멀", "포멀"],
                    "추천문구": "회식에는 니트와 슬랙스에 체스터 코트를 매치하시면 깔끔해 보이실 거예요."
                }'''
            },
            {
                "input": "캠퍼스 개강파티 옷 추천",
                "output": '''{
                    "키워드": ["캠퍼스", "개강파티", "셔츠", "데님", "스니커즈", "크로스백"],
                    "스타일": ["캐주얼", "스마트캐주얼", "내추럴"],
                    "추천문구": "개강파티에는 셔츠와 데님에 스니커즈로 편하면서도 단정하게 연출해 보세요."
                }'''
            }
        ]
        
        # 프롬프트 구성
        self._setup_prompts()
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{input}"),
            ("ai", "{output}")
        ])
        
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=self.examples
        )
        
        self.final_prompt = ChatPromptTemplate.from_messages([
            ("system", """너는 한국어 패션 비서야.

            다음 지침을 따라줘:
            1) 사용자의 질문을 이해하고, 현재 날씨와 상황을 고려해.
            2) 핵심 키워드는 5~6개(장소, 상황)과 스타일은 {cloth_attr} 에 있는 정보로 3~5개 키워드를 뽑아.
            3) 키워드와 스타일은 중복 없이 다양하게 선택해.
            4) 짧고 자연스러운 존댓말 추천 문구를 작성해.
            5) 사용자의 성별은 {gender} 야
            6) 현재 날씨를 고려하여 옷 조합을 추천해줘

            {context}

            {format_instructions}

            출력은 반드시 JSON 형식으로만 해줘."""),
            few_shot_prompt,
            ("human", "{input}")
        ])
    
    def search_similar_queries(self, query: str, k: int = 3) -> List[dict]:
        """유사한 과거 질문 검색"""
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            similar_queries = []
            
            for doc, score in results:
                # 문자열로 저장된 키워드와 스타일을 다시 리스트로 변환
                keywords_str = doc.metadata.get("keywords", "")
                styles_str = doc.metadata.get("styles", "")
                
                keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []
                styles = [s.strip() for s in styles_str.split(',')] if styles_str else []
                
                similar_queries.append({
                    "query": doc.metadata.get("query", ""),
                    "keywords": keywords,
                    "styles": styles,
                    "recommendation": doc.metadata.get("recommendation", ""),
                    "similarity_score": score
                })
            
            return similar_queries
        except Exception as e:
            print(f"검색 중 오류: {e}")
            return []
    
    def save_to_vectorstore(self, query: str, result: dict):
        """추천 결과를 벡터 DB에 저장"""
        try:
            # 문서 내용 구성 (검색을 위한 풍부한 텍스트)
            content = f"""질문: {query}
                        키워드: {', '.join(result['키워드'])}
                        스타일: {', '.join(result['스타일'])}
                        추천: {result['추천문구']}"""
            
            # 메타데이터 구성 (ChromaDB는 리스트를 직접 저장할 수 없으므로 문자열로 변환)
            metadata = {
                "query": query,
                "keywords": ', '.join(result['키워드']),  # 리스트를 문자열로 변환
                "styles": ', '.join(result['스타일']),    # 리스트를 문자열로 변환
                "recommendation": result['추천문구']
            }
            
            # 문서 생성
            document = Document(
                page_content=content,
                metadata=metadata
            )
            
            # 복잡한 메타데이터 필터링 (안전장치)
            filtered_docs = filter_complex_metadata([document])
            
            # 벡터 DB에 저장
            self.vectorstore.add_documents(filtered_docs)
            print(f"벡터 DB에 저장 완료")
            
        except Exception as e:
            print(f"저장 중 오류: {e}")
    
    def chat_answer(self, user_text: str, use_history: bool = True) -> dict:
        """패션 추천 생성"""
        context = ""
        
        # 유사한 과거 질문 검색 (선택적)
        if use_history:
            similar = self.search_similar_queries(user_text, k=2)
            if similar:
                context = "참고할 만한 과거 추천:\n"
                for i, item in enumerate(similar, 1):
                    if item['similarity_score'] < 1.5:  # 유사도가 높을 때만
                        context += f"{i}. {item['query']}: {', '.join(item['keywords'][:3])}\n"
                context += "\n위 내용과 중복되지 않는 새로운 추천을 해줘.\n"
        
        # 체인 구성 및 실행
        chain = self.final_prompt | self.llm | self.parser
        user = session.get("user")
        cloth_attr = get_user_clothing_with_attributes(user['useridseq'])
        # print(cloth_attr)
        # print(user)
        
        try:
            result = chain.invoke({
                "input": user_text,
                "context": context,
                "format_instructions": self.parser.get_format_instructions(),
                "gender": user['gender'],
                "cloth_attr": cloth_attr
            })
        except Exception as e:
            print(f"파싱 오류: {e}")
            # structured output 사용
            llm_structured = self.llm.with_structured_output(FashionRecommendation)
            chain_structured = self.final_prompt | llm_structured
            result = chain_structured.invoke({
                "input": user_text,
                "context": context,
                "format_instructions": "",
                "gender": "",
                "cloth_attr": ""
            })
            result = result.dict()
        
        # 결과를 벡터 DB에 저장
        self.save_to_vectorstore(user_text, result)
        
        return result

# 구글 STT
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("듣는중...")
        audio = r.listen(source)
        said = ""
        
        try:
            said = r.recognize_google(audio, language='ko-KR')
        except Exception as e:
            print("예외:" + str(e))
            
        return said

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUT_DIR = os.path.join(BASE_DIR, "tts_outputs")

# edge tts
def speak_edge(answer, voice="ko-KR-SoonBokNeural", rate="+8%", pitch="+5Hz"):
    """
    - voice: 목소리 이름 - 현재 설정값은 여성의 부드러운 말투
    - rate: 속도 ('+20%', '-10%' 등)
    - pitch: 피치 ('+5Hz', '-3Hz' 등)
    """
    
    os.makedirs(OUT_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(OUT_DIR, filename)
    
    async def _run_tts():
        communicate = edge_tts.Communicate(
            answer,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        await communicate.save(filepath)

        # playsound.playsound(filename)
        # os.remove(filename)
        
    asyncio.run(_run_tts())
    return filename

# stt post 결과 보내기
@chat_bp.route("/stt", methods=["POST"])
def get_audio_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    print(data)
    
    # 패션어시스턴트 초기화
    assistant = FashionAssistant(persist_directory="./fashion_chroma_db")
    
    # 챗봇 답변
    result = assistant.chat_answer(data)
    
    # 결과 추출
    keywords = result.get("키워드", [])
    styles = result.get("스타일", [])
    text = result.get("추천문구", "")

    # tts 변환
    filename = speak_edge(text)
    
    return jsonify({"ok": True, "keywords": keywords, 
                    "styles": styles, "text": text,
                    "tts_url": f"/api/voice/tts/{filename}"})

# tts 결과 get으로 보내기
@chat_bp.route("/tts/<path:filename>", methods=["GET"])
def serve_tts(filename):
        # 보안 처리
    safe_name = secure_filename(filename)
    path = os.path.join(OUT_DIR, safe_name)

    if not (safe_name and os.path.exists(path)):
        return jsonify({"ok": False, "error": "file not found"}), 404

    # 파일 전송
    resp = send_file(
        path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=safe_name,
        conditional=True,  # Range 요청 등 지원
        etag=False,
        last_modified=None,
        max_age=0
    )
    # 캐시 방지
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

    # 전송이 끝난 뒤 파일 삭제
    @resp.call_on_close
    def _cleanup():
        try:
            os.remove(path)
        except Exception:
            pass

    return resp


if __name__ == "__main__":
    # 패션 어시스턴트 초기화
    assistant = FashionAssistant(persist_directory="./fashion_chroma_db")
    
    # 음성 입력 받기 (실제 사용 시)
    # user_text = get_audio()
    
    # 테스트용 텍스트 입력
    # user_text = "결혼 하객룩으로 추천해줘"
    user_text = get_audio_text # 리액트에서 받아온 user 음성 text
    print(f"사용자: {user_text}\n")
    
    # 챗봇 답변 생성
    result = assistant.chat_answer(user_text)
    
    # 결과 추출
    keywords = result.get("키워드", [])
    styles = result.get("스타일", [])
    text = result.get("추천문구", "")
    
    # 결과 출력
    print("=" * 60)
    print(f"키워드: {keywords}")
    print(f"스타일: {styles}")
    print(f"추천문구: {text}")
    print("=" * 60)
    
    # 음성 출력 (실제 사용 시), 프론트에 전달할 때는 voice.mp3를 넘겨서 처리해야함
    # speak_edge(text)
    
    # 유사 질문 검색 테스트
    print("\n과거 유사 질문 검색:")
    similar = assistant.search_similar_queries(user_text, k=3)
    for i, item in enumerate(similar, 1):
        print(f"{i}. {item['query']} (유사도: {item['similarity_score']:.4f})")
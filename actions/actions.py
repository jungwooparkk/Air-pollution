import mysql.connector
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import difflib
from googletrans import Translator

class ActionChatBot(Action):

    def name(self) -> Text:
        return "action_chatbot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        original_message = tracker.latest_message.get('text')
        translator = Translator()

        # 언어 감지 및 번역
        detected_lang = translator.detect(original_message).lang
        translated_msg = original_message
        if detected_lang != 'ko':
            translated_msg = translator.translate(original_message, src=detected_lang, dest='ko').text

        # DB 연결
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='rasa_core'
        )
        cursor = conn.cursor()

        # 이미지 ID 매핑
        category_image_ids = {
            "일반 규칙": 1,
            "기숙사 시설 이용": 2,
            "주의사항 (화재)": 3,
            "주의사항 (화상)": 4,
            "기타 주의사항": 5,
            "금지 행위": 6,
            "상벌 제도": 7,
            "세탁 카페": 8,
            "버스 시간표": 9,
            "연락처 정보": 10
        }

        try:
            # 연락처 카테고리 목록
            if "연락처 목록" in translated_msg or "연락처 카테고리" in translated_msg or "연락처 종류" in translated_msg:
                query = "SELECT DISTINCT `구분` FROM number"
                cursor.execute(query)
                rows = cursor.fetchall()

                if rows:
                    categories = [row[0] for row in rows]
                    result = "\n- " + "\n- ".join(categories)
                    message = f"\ud83d\udcde 현재 등록된 연락처 카테고리는 다음과 같습니다:\n{result}"
                else:
                    message = "연락처 카테고리가 등록되어 있지 않습니다."
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # 규칙 카테고리 목록
            if "규칙" in translated_msg or "규칙 리스트" in translated_msg or "카테고리" in translated_msg:
                query = "SELECT DISTINCT `구분 (Category)` FROM chatbot"
                cursor.execute(query)
                rows = cursor.fetchall()

                if rows:
                    categories = [row[0] for row in rows]
                    result = "\n- " + "\n- ".join(categories)
                    message = f"\ud83d\udcda 현재 가능한 규칙 카테고리는 다음과 같습니다:\n{result}"
                else:
                    message = "등록된 카테고리가 없습니다."
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # 규칙 카테고리 판별
            category = None
            if "일반 규칙" in translated_msg:
                category = "일반 규칙"
            elif "기숙사 시설 이용" in translated_msg or "기숙사" in translated_msg:
                category = "기숙사 시설 이용"
            elif "주의사항 (화재)" in translated_msg or "화재" in translated_msg:
                category = "주의사항 (화재)"
            elif "주의사항 (화상)" in translated_msg or "화상" in translated_msg:
                category = "주의사항 (화상)"
            elif "기타 주의사항" in translated_msg or "기타" in translated_msg:
                category = "기타 주의사항"
            elif "금지 행위" in translated_msg or "금지" in translated_msg:
                category = "금지 행위"
            elif "상벌 제도" in translated_msg or "상벌" in translated_msg:
                category = "상벌 제도"
            elif "세탁 카페" in translated_msg or "세탁" in translated_msg:
                category = "세탁 카페"
            elif "버스 시간표" in translated_msg or "버스" in translated_msg:
                category = "버스 시간표"

            # 연락처 구분 유사 매칭
            query = "SELECT DISTINCT `구분` FROM number"
            cursor.execute(query)
            all_categories = [row[0] for row in cursor.fetchall()]

            matched_category = None
            matches = difflib.get_close_matches(translated_msg, all_categories, n=1, cutoff=0.5)
            if matches:
                matched_category = matches[0]
            else:
                for cat in all_categories:
                    if cat in translated_msg or translated_msg in cat:
                        matched_category = cat
                        break

            if matched_category:
                if matched_category in category_image_ids:
                    dispatcher.utter_message(image=f"http://127.0.0.1:8080/image/{category_image_ids[matched_category]}")
                else:
                    query_img = "SELECT image_id FROM rule_images WHERE category = %s"
                    cursor.execute(query_img, (matched_category,))
                    image_rows = cursor.fetchall()
                    if image_rows:
                        for image_row in image_rows:
                            dispatcher.utter_message(image=f"http://127.0.0.1:8080/image/{image_row[0]}")

                query = "SELECT `세부항목`, `상세내용` FROM number WHERE `구분` = %s"
                cursor.execute(query, (matched_category,))
                rows = cursor.fetchall()

                if rows:
                    lines = [f"- {row[0]} → {row[1]}" for row in rows]
                    result = "\n".join(lines)
                    message = f"\ud83d\udcde [{matched_category}] 연락처 세부항목 목록입니다:\n{result}"
                else:
                    message = "해당 구분에 연락처 세부항목이 없습니다."
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # 규칙 세부 내용 + 이미지 먼저 출력
            if category:
                if category in category_image_ids:
                    dispatcher.utter_message(image=f"http://127.0.0.1:8080/image/{category_image_ids[category]}")
                else:
                    query_img = "SELECT image_id FROM rule_images WHERE category = %s"
                    cursor.execute(query_img, (category,))
                    image_rows = cursor.fetchall()
                    if image_rows:
                        for image_row in image_rows:
                            dispatcher.utter_message(image=f"http://127.0.0.1:8080/image/{image_row[0]}")

                query = "SELECT `세부 항목 (Sub-category/Item)`, `상세 내용 (Details)` FROM chatbot WHERE `구분 (Category)` = %s"
                cursor.execute(query, (category,))
                rows = cursor.fetchall()

                if rows:
                    lines = [f"- {sub_item} → {detail}" for sub_item, detail in rows]
                    result = "\n".join(lines)
                    message = f"\ud83d\udcda [{category} 안내]\n{result}"
                else:
                    message = "해당 규칙을 찾을 수 없습니다."
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # 연락처 세부항목 직접 매칭
            query = "SELECT `세부항목`, `상세내용` FROM number"
            cursor.execute(query)
            all_sub_items = cursor.fetchall()

            matched_sub_item = None
            for sub_item, detail in all_sub_items:
                if sub_item in translated_msg or translated_msg in sub_item:
                    matched_sub_item = (sub_item, detail)
                    break

            if matched_sub_item:
                sub_name, sub_detail = matched_sub_item
                message = f"{sub_detail}"
                final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
                dispatcher.utter_message(text=final_msg)
                return []

            # 처리 실패
            message = "죄송해요. 해당 내용을 이해하지 못했어요. 다시 질문해 주세요."
            final_msg = translator.translate(message, src='ko', dest=detected_lang).text if detected_lang != 'ko' else message
            dispatcher.utter_message(text=final_msg)
            return []

        finally:
            cursor.close()
            conn.close()
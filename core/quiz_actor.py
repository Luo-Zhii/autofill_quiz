import random
import time
import re
from thefuzz import fuzz, process
from playwright.sync_api import Page

# Mapping từ chữ cái đáp án sang giá trị radio button.
ANSWER_MAP: dict[str, str] = {"A": "0", "B": "1", "C": "2", "D": "3"}
NEXT_BUTTON_SELECTOR = "#mod_quiz-next-nav"

class QuizActor:
    def __init__(self, page: Page, test_data=None, source_file: str = "Unknown") -> None:
        self._page = page
        self.test_data = test_data or []
        self.source_file = source_file
        # CỰC KỲ QUAN TRỌNG: Lưu danh sách ID đã dùng xuyên suốt các trang.
        self.used_ids = set()

    def _safe_click(self, element, label_element=None) -> bool:
        """Chiến thuật click 3 lớp để xuyên thủng các lớp phủ CSS của Moodle."""
        try:
            element.click(force=True, timeout=2000); return True
        except Exception:
            try:
                if label_element: label_element.click(force=True, timeout=2000); return True
            except Exception:
                try: element.dispatch_event("click"); return True
                except Exception: return False

    def get_all_question_groups(self) -> list[str]:
        # Cuộn xuống cuối trang để ép Moodle render hết các câu hỏi (tránh Lazy Loading)
        self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1) 
        
        all_radios = self._page.query_selector_all("input[type='radio'].form-check-input")
        seen, group_names = set(), []
        for r in all_radios:
            name = r.get_attribute("name")
            if name and name not in seen:
                seen.add(name); group_names.append(name)
        return group_names

    def fill_all_questions_intelligently(self) -> None:
        # Chỉ đợi DOMContentLoaded để tránh kẹt mạng (networkidle)
        try:
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        except: pass

        group_names = self.get_all_question_groups()
        if not group_names: 
            print("[QuizActor] No questions found. Retrying in 2s...")
            time.sleep(2)
            group_names = self.get_all_question_groups()
            if not group_names: return

        print(f"[QuizActor] STARTING SCAN. Memory: {len(self.used_ids)} answered.")

        visual_groups = []
        for name in group_names:
            el = self._page.query_selector(f"input[name='{name}']")
            box = el.bounding_box() if el else None
            if box: visual_groups.append({"name": name, "x": box["x"], "y": box["y"]})
        
        # Sắp xếp theo tọa độ để làm bài tự nhiên từ trên xuống
        sorted_groups = sorted(visual_groups, key=lambda g: (round(g["x"] / 50), g["y"]))

        for group in sorted_groups:
            name = group["name"]
            try:
                all_radios = self._page.query_selector_all(f"input[name='{name}']")
                web_options = []
                for r in all_radios:
                    r_id = r.get_attribute("id")
                    lbl = self._page.query_selector(f"label[for='{r_id}']")
                    if lbl: web_options.append({"text": lbl.inner_text().strip(), "el": r, "lbl": lbl})

                if not web_options: continue
                web_texts = [opt["text"] for opt in web_options]

                # BƯỚC 1: QUÉT DATABASE ĐỂ TÌM CÂU HỎI PHÙ HỢP
                matched_data = None
                for item in self.test_data:
                    if item.get("id") in self.used_ids: continue
                    
                    db_ans = item.get("correct_answer_text", "")
                    # Dùng token_set_ratio để tìm đúng 'ngữ cảnh' câu hỏi trong Pool
                    res = process.extractOne(db_ans, web_texts, scorer=fuzz.token_set_ratio)
                    if res and res[1] >= 95:
                        matched_data = item
                        break

                if not matched_data: continue

                target_id = matched_data.get("id")
                correct_ans = matched_data["correct_answer_text"]

                # BƯỚC 2: CHỌN ĐÁP ÁN (Dùng fuzz.ratio để đảm bảo KHÔNG LỆCH chữ 'more', 'less'...)
                # Strict matching to distinguish between 'energetically' and 'more energetically'.
                final_res = process.extractOne(correct_ans, web_texts, scorer=fuzz.ratio)
                
                if final_res and final_res[1] >= 85: # Ngưỡng an toàn cao
                    best = next(o for o in web_options if o["text"] == final_res[0])
                    # Cuộn đến câu hỏi để tránh bị các thành phần dính (sticky) che khuất
                    best["el"].scroll_into_view_if_needed()
                    if self._safe_click(best["el"], best["lbl"]):
                        print(f"[QuizActor] [OK] {target_id} -> {final_res[0]} (DB: {correct_ans})")
                        self.used_ids.add(target_id)

                time.sleep(random.uniform(0.1, 0.2))
            except Exception as e:
                print(f"[QuizActor] Error {name}: {e}")

    def has_next_page(self) -> bool: return self._page.is_visible(NEXT_BUTTON_SELECTOR)
    
    def click_next_page(self) -> None:
        print("[QuizActor] Moving to next page...")
        try:
            self._page.wait_for_selector(NEXT_BUTTON_SELECTOR, state="visible", timeout=5000)
            # Click và đợi domcontentloaded thay vì networkidle để chống timeout
            self._page.click(NEXT_BUTTON_SELECTOR, force=True)
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            self._page.wait_for_timeout(2000) # Nghỉ 2s để trang ổn định
        except Exception as e:
            print(f"[QuizActor] Next Page navigation failed: {e}")
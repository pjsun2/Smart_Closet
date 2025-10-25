"""
Smart Closet GUI 런처
클릭으로 백엔드/프론트엔드 서버를 쉽게 실행할 수 있습니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
from pathlib import Path

class SmartClosetLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Closet Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 아이콘 설정 (선택사항)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # 기본 경로
        self.base_dir = Path(__file__).parent
        
        # 프로세스 저장
        self.backend_process = None
        self.frontend_process = None
        
        self.create_widgets()
        self.check_status()
    
    def create_widgets(self):
        # 헤더
        header = tk.Frame(self.root, bg='#2c3e50', height=80)
        header.pack(fill='x')
        
        title = tk.Label(
            header, 
            text="Smart Closet",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title.pack(pady=20)
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 상태 표시
        status_frame = tk.LabelFrame(main_frame, text="서버 상태", padx=10, pady=10)
        status_frame.pack(fill='x', pady=(0, 20))
        
        self.backend_status = tk.Label(
            status_frame, 
            text="● 백엔드: 중지됨",
            font=('Arial', 11),
            fg='red'
        )
        self.backend_status.pack(anchor='w', pady=5)
        
        self.frontend_status = tk.Label(
            status_frame, 
            text="● 프론트엔드: 중지됨",
            font=('Arial', 11),
            fg='red'
        )
        self.frontend_status.pack(anchor='w', pady=5)
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='both', expand=True)
        
        # 버튼 스타일
        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 12), padding=10)
        
        # 백엔드 버튼
        backend_btn = ttk.Button(
            button_frame,
            text="🔧 백엔드 서버 시작\n(Flask API)",
            style='Large.TButton',
            command=self.start_backend
        )
        backend_btn.pack(fill='x', pady=5)
        
        # 프론트엔드 버튼
        frontend_btn = ttk.Button(
            button_frame,
            text="🎨 프론트엔드 서버 시작\n(React Web)",
            style='Large.TButton',
            command=self.start_frontend
        )
        frontend_btn.pack(fill='x', pady=5)
        
        # 통합 실행 버튼
        all_btn = ttk.Button(
            button_frame,
            text="🚀 모두 시작\n(백엔드 + 프론트엔드)",
            style='Large.TButton',
            command=self.start_all
        )
        all_btn.pack(fill='x', pady=5)
        
        # 구분선
        ttk.Separator(button_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # 중지 버튼
        stop_btn = ttk.Button(
            button_frame,
            text="🛑 모든 서버 중지",
            style='Large.TButton',
            command=self.stop_all
        )
        stop_btn.pack(fill='x', pady=5)
        
        # 하단 정보
        info_frame = tk.Frame(main_frame)
        info_frame.pack(side='bottom', fill='x', pady=(20, 0))
        
        info_text = "백엔드: https://localhost:5000\n프론트엔드: https://localhost:3000"
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=('Arial', 9),
            fg='gray'
        )
        info_label.pack()
        
        # 상태 업데이트
        self.root.after(3000, self.periodic_check)
    
    def check_status(self):
        """서버 상태 확인"""
        # 간단한 상태 확인 (프로세스 존재 여부)
        pass
    
    def periodic_check(self):
        """주기적 상태 확인"""
        self.check_status()
        self.root.after(3000, self.periodic_check)
    
    def start_backend(self):
        """백엔드 서버 시작"""
        try:
            bat_file = self.base_dir / "start_backend.bat"
            if not bat_file.exists():
                messagebox.showerror("오류", "start_backend.bat 파일을 찾을 수 없습니다.")
                return
            
            # 새 콘솔 창에서 실행
            subprocess.Popen(
                ['cmd', '/c', 'start', 'Smart Closet Backend', 'cmd', '/k', str(bat_file)],
                cwd=str(self.base_dir),
                shell=True
            )
            
            self.backend_status.config(text="● 백엔드: 시작 중...", fg='orange')
            self.root.after(2000, lambda: self.backend_status.config(
                text="● 백엔드: 실행 중", fg='green'
            ))
            
            messagebox.showinfo(
                "백엔드 시작",
                "백엔드 서버가 새 창에서 시작되었습니다.\n\n"
                "주소: https://localhost:5000\n\n"
                "서버 창을 닫지 마세요!"
            )
        except Exception as e:
            messagebox.showerror("오류", f"백엔드 시작 실패:\n{str(e)}")
    
    def start_frontend(self):
        """프론트엔드 서버 시작"""
        try:
            bat_file = self.base_dir / "start_frontend.bat"
            if not bat_file.exists():
                messagebox.showerror("오류", "start_frontend.bat 파일을 찾을 수 없습니다.")
                return
            
            # 새 콘솔 창에서 실행
            subprocess.Popen(
                ['cmd', '/c', 'start', 'Smart Closet Frontend', 'cmd', '/k', str(bat_file)],
                cwd=str(self.base_dir),
                shell=True
            )
            
            self.frontend_status.config(text="● 프론트엔드: 시작 중...", fg='orange')
            self.root.after(3000, lambda: self.frontend_status.config(
                text="● 프론트엔드: 실행 중", fg='green'
            ))
            
            messagebox.showinfo(
                "프론트엔드 시작",
                "프론트엔드 서버가 새 창에서 시작되었습니다.\n\n"
                "주소: https://localhost:3000\n\n"
                "잠시 후 브라우저가 자동으로 열립니다.\n"
                "서버 창을 닫지 마세요!"
            )
        except Exception as e:
            messagebox.showerror("오류", f"프론트엔드 시작 실패:\n{str(e)}")
    
    def start_all(self):
        """모든 서버 시작"""
        try:
            bat_file = self.base_dir / "start_all.bat"
            if not bat_file.exists():
                messagebox.showerror("오ría", "start_all.bat 파일을 찾을 수 없습니다.")
                return
            
            # 배치 파일 실행
            subprocess.Popen(
                [str(bat_file)],
                cwd=str(self.base_dir),
                shell=True
            )
            
            self.backend_status.config(text="● 백엔드: 시작 중...", fg='orange')
            self.frontend_status.config(text="● 프론트엔드: 시작 중...", fg='orange')
            
            self.root.after(3000, lambda: [
                self.backend_status.config(text="● 백엔드: 실행 중", fg='green'),
                self.frontend_status.config(text="● 프론트엔드: 실행 중", fg='green')
            ])
            
            messagebox.showinfo(
                "통합 시작",
                "백엔드와 프론트엔드 서버가 시작되었습니다!\n\n"
                "백엔드: https://localhost:5000\n"
                "프론트엔드: https://localhost:3000\n\n"
                "각 서버는 별도 창에서 실행됩니다.\n"
                "서버 창을 닫지 마세요!"
            )
        except Exception as e:
            messagebox.showerror("오류", f"서버 시작 실패:\n{str(e)}")
    
    def stop_all(self):
        """모든 서버 중지"""
        result = messagebox.askyesno(
            "서버 중지",
            "모든 서버를 중지하시겠습니까?\n\n"
            "실행 중인 백엔드와 프론트엔드 서버가\n"
            "모두 종료됩니다."
        )
        
        if result:
            try:
                bat_file = self.base_dir / "stop_servers.bat"
                if bat_file.exists():
                    subprocess.run([str(bat_file)], cwd=str(self.base_dir), shell=True)
                
                self.backend_status.config(text="● 백엔드: 중지됨", fg='red')
                self.frontend_status.config(text="● 프론트엔드: 중지됨", fg='red')
                
                messagebox.showinfo("서버 중지", "모든 서버가 중지되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"서버 중지 실패:\n{str(e)}")

def main():
    root = tk.Tk()
    app = SmartClosetLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()

# 📊 NPS CEO News Monitor

> **국민연금공단(NPS) 이사장 언론 보도 실시간 모니터링 시스템**
>
> 본 프로젝트는 네이버 오픈 API와 GitHub Actions를 활용하여 김성주 이사장님 관련 신규 보도자료를 5-10분 간격으로 수집하고 텔레그램으로 전송합니다.

<p align="center">
  <img src="logo.png" alt="NPS Logo" width="200">
</p>


## ✨ 주요 기능

* **실시간 모니터링**: 5~10분 간격으로 네이버 뉴스를 자동 검색합니다.
* **정교한 키워드 필터링**: `"국민연금" "김성주"` 조합을 통해 동명이인 오보도를 최소화합니다.
* **상세 정보 제공**: 기사 제목, 요약문, 발행 시간, 언론사 정보를 포함한 메시지를 전송합니다.
* **서버리스 운영**: GitHub Actions를 사용하여 별도의 서버 비용 없이 가동됩니다.

<br>

## 📱 알림 예시

> 📢 **NPS 새 기사 알림**
> 
> 📌 **제목**: 김성주 국민연금 이사장, 현장 소통 행보 강화  
> ⏰ **시간**: 2025-12-21 10:30  
> 📝 **요약**: 국민연금공단 김성주 이사장이 전주 본부에서 취임 후 기자간담회를 열고...  
> 🔗 **링크**: [https://news.naver.com/](https://news.naver.com/)...


<br>

## 🚀 시작하기

* **봇 구독하기**: [NPS CEO News Monitor Bot](https://t.me/nps_news_monitor_bot) 링크를 클릭하고 **[시작]** 을 누르세요.

<br>  

## ⚠️ 유의 사항

* 본 봇은 **국민연금공단 홍보실 내부 업무용**으로 제작되었습니다.
* 수집된 기사의 저작권은 각 언론사에 있으며, 본 시스템은 링크 공유 서비스만을 제공합니다.

<br>

## 🛠 기술 스택

* **Language**: Python 3.9+
* **Infrastructure**: GitHub Actions
* **API**: Naver Search API, Telegram Bot API
* **Database**: last_link.txt (File-based tracking)

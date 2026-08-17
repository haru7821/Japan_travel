# 이메일 로그인 · 스탬프 클라우드 동기화 설정 가이드

이 사이트는 기본적으로 완전한 정적 사이트(GitHub Pages, 서버 없음)입니다.
찜(스탬프)은 원래 브라우저 localStorage에만 저장돼 기기·브라우저마다 따로
남습니다. 이 가이드를 따라 **Firebase**(구글의 무료 백엔드 서비스)를 연결하면,
사용자가 이메일로 로그인해서 **어느 기기에서든 같은 스탬프**를 볼 수 있게
됩니다.

**설정하지 않아도** 사이트는 지금처럼 완전히 정상 작동합니다. 로그인 버튼
(🎫)은 설정 전까지 자동으로 숨겨져 있습니다.

---

## 1단계 — Firebase 프로젝트 만들기 (5~10분, 무료)

1. [https://console.firebase.google.com](https://console.firebase.google.com) 접속 후 구글 계정으로 로그인
2. "프로젝트 추가" → 프로젝트 이름 입력(예: `japan-travel-guide`) → 애널리틱스는 꺼도 무방 → 프로젝트 생성
3. 왼쪽 메뉴 **Authentication** → "시작하기" → **로그인 방법** 탭 → **이메일 링크(비밀번호 없는 로그인)** 사용 설정
4. 왼쪽 메뉴 **Firestore Database** → "데이터베이스 만들기" → 위치는 `asia-northeast3`(서울) 권장 → **프로덕션 모드**로 시작
5. Firestore가 만들어지면 **규칙(Rules)** 탭으로 이동해 아래 내용으로 전체 교체 후 게시:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /stamps/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /reviews/{reviewId} {
      allow read: if true;
      allow create: if request.auth != null
                    && request.resource.data.authorId == request.auth.uid
                    && request.resource.data.title is string
                    && request.resource.data.title.size() > 0
                    && request.resource.data.title.size() <= 60
                    && request.resource.data.body is string
                    && request.resource.data.body.size() > 0
                    && request.resource.data.body.size() <= 2000
                    && request.resource.data.region in ['fukuoka','osaka','tokyo','sapporo','kyoto'];
      allow update: if false;
      allow delete: if request.auth != null && resource.data.authorId == request.auth.uid;
    }
  }
}
```

이 규칙은 두 가지입니다:
- **스탬프**: 로그인한 본인만 자기 스탬프 문서를 읽고 쓸 수 있습니다. 다른 사람의
  데이터는 볼 수 없습니다.
- **여행 후기**: 누구나 읽을 수 있지만, 글쓰기·삭제는 로그인한 본인 글에만
  허용됩니다(제목 60자·내용 2,000자 이내로 서버 단에서도 강제). 수정은 막아뒀습니다
  (다시 쓰려면 삭제 후 새로 작성).

6. 왼쪽 상단 톱니바퀴 → **프로젝트 설정** → 아래로 스크롤 → "내 앱" → **</> (웹)** 아이콘 클릭 → 앱 닉네임 입력 → 앱 등록
7. 화면에 나오는 `firebaseConfig` 객체를 복사(아래처럼 생긴 값입니다):

```js
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "japan-travel-guide.firebaseapp.com",
  projectId: "japan-travel-guide",
  storageBucket: "japan-travel-guide.firebasestorage.app",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef..."
};
```

8. **Authentication → Settings → 승인된 도메인**에 실제 배포 도메인
   (`haru7821.github.io`)이 포함돼 있는지 확인 — 기본적으로 자동 포함되지만
   커스텀 도메인을 쓴다면 직접 추가해야 합니다.

---

## 2단계 — 이 저장소에 키 넣기

`index.html`에서 `FIREBASE_API_KEY_PLACEHOLDER` 등 6개 플레이스홀더 문자열을
찾아(검색: `PLACEHOLDER`) 7단계에서 복사한 실제 값으로 각각 바꿉니다.

```js
var FIREBASE_CONFIG = {
  apiKey: 'FIREBASE_API_KEY_PLACEHOLDER',            // ← 여기
  authDomain: 'FIREBASE_AUTH_DOMAIN_PLACEHOLDER',     // ← 여기
  projectId: 'FIREBASE_PROJECT_ID_PLACEHOLDER',       // ← 여기
  storageBucket: 'FIREBASE_STORAGE_BUCKET_PLACEHOLDER', // ← 여기
  messagingSenderId: 'FIREBASE_SENDER_ID_PLACEHOLDER',  // ← 여기
  appId: 'FIREBASE_APP_ID_PLACEHOLDER'                // ← 여기
};
```

저장 후 `git commit` → `git push`. 반영되면 로그인 버튼(🎫)이 자동으로
나타납니다.

---

## 3단계 — 확인

1. 배포된 사이트에서 우측 상단 🎫 버튼 클릭
2. 본인 이메일 입력 → "로그인 링크 받기"
3. 받은 메일함(스팸함도 확인)에서 링크 클릭 → 자동으로 로그인 완료
4. 아무 카드나 ♥ 눌러 찜 → 다른 브라우저(또는 시크릿 모드)에서 같은 이메일로
   로그인 → 스탬프가 그대로 나타나면 정상 작동 중인 것입니다.
5. 내비게이션의 "✍️ 여행 후기" 클릭 → 지역을 골라 후기 작성 → 등록되면
   목록에 바로 뜨는지, 지역 필터 탭으로 걸러지는지 확인. 로그인 상태에서는
   본인이 쓴 글에만 삭제 버튼이 보입니다.

---

## 참고 — 클로드 아티팩트에서는 왜 로그인이 안 되나요?

이 사이트는 GitHub Pages(라이브 사이트)와 claude.ai 아티팩트(미리보기)
두 곳에 동시에 배포됩니다. 아티팩트는 보안 정책상 외부 스크립트(CDN) 로드를
전면 차단하는데, Firebase는 구글 CDN에서 스크립트를 불러와야 하므로
**아티팩트 미리보기에서는 로그인 기능이 자동으로 비활성화**됩니다(에러 없이
조용히 숨김 처리). 실제 배포 사이트(`haru7821.github.io`)에서는 정상
작동합니다.

## 참고 — 비용

Firebase Authentication과 Firestore 모두 이 정도 사용량(개인 여행 가이드
사이트)에서는 **무료 티어(Spark 플랜)로 충분**합니다. 별도 결제 등록 없이도
바로 사용할 수 있습니다.

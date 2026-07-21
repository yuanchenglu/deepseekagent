---
name: douyin-publisher
description: Publish articles to Douyin (抖音) platform with optimized formatting for short-video and图文 content. Handles content adaptation, image/video generation, and API publishing.
triggers:
  - User wants to publish to Douyin
  - User says "发抖音"
  - User mentions douyin or 抖音 publishing
  - Batch publishing to multiple platforms including Douyin
---

# Douyin (抖音) Publisher

## Overview

Dedicated skill for publishing content to Douyin platform. Supports both:
- **图文 (Image-Text)**: Static images with text overlay
- **视频 (Video)**: Short-form video content

Adapts content to fit Douyin's fast-paced, entertainment-focused style.

## Platform Characteristics

### Content Style
- **Title**: Attention-grabbing,悬念-driven (e.g., "最后3秒惊到我了！")
- **Format**: Very short, punchy sentences
- **Music**: Background music is crucial for engagement
- **Visuals**: High contrast, bright colors, dynamic visuals
- **Hooks**: First 3 seconds must grab attention
- **Length**: 15-60 seconds optimal for video; 3-5 images for 图文

### Image/Video Requirements
- **Ratio**: 9:16 (vertical) mandatory for full-screen experience
- **Size**: 1080×1920px (9:16)
- **Style**: High energy, trending aesthetics, bold text overlays
- **Text**: Large, readable text overlays with effects

### API Requirements
- Douyin Open Platform API (抖音开放平台)
- Requires: app_id, app_secret, access_token
- Content must comply with platform guidelines

## User Configuration

To be configured when user provides credentials:
- **App ID**: From Douyin Open Platform
- **App Secret**: From Douyin Open Platform
- **Access Token**: OAuth2 token for publishing

## Content Adaptation Rules

### Title Adaptation
```
WeChat Title: "不会写代码也能做应用？我试了这个工具，30分钟搞定一个完整项目"
↓
Douyin Title Options:
1. "30分钟做出一个App！最后效果惊到我了"
2. "不会代码的我，30分钟后做出了这个..."
3. "我说了一句话，30分钟后👇"

Rules:
- Create suspense/curiosity
- Use cliffhangers ("最后3秒", "看到最后", "结果...")
- Keep it short and punchy
- Use visual indicators (👇, 🔥, 💥)
```

### Content Adaptation (图文 Format)
```
Original: Long detailed article
↓
Douyin 图文 Format (3-5 slides):

Slide 1 (Cover):
[Bold headline with effect]
"30分钟做出一个App！"
[Eye-catching background]

Slide 2 (Problem):
"不会写代码？"
"没关系！"
[Relatable image]

Slide 3 (Solution):
"这个工具"
"一句话搞定"
[Tool screenshot/demo]

Slide 4 (Result):
"30分钟后..."
[Final product showcase]

Slide 5 (CTA):
"你也想试试？"
"评论区告诉我"
[Call to action]
```

### Content Adaptation (Video Format)
```
Video Script Structure (30-60 seconds):

0-3s: Hook
"你不会还在手动写代码吧？"
[Shocking/curious visual]

3-15s: Problem
"以前我想做个App"
"得学编程、找开发"
"费时又费钱..."
[Frustration visuals]

15-40s: Solution
"直到我发现了这个"
"只需要说一句话..."
[Demo of tool]
"30分钟后"
[Results showing]

40-55s: Proof/Social Proof
"你看这就是成品"
"完全不用写代码"
[Showcasing features]

55-60s: CTA
"想要工具的"
"评论区扣1"
[Pointing to comments]
```

## Publishing Workflow

```
User provides article
    ↓
1. Extract core value proposition and hook
    ↓
2. Adapt for Douyin format:
   - Create suspenseful title
   - Break into 3-5 slides (图文) or script (视频)
   - Add trending music suggestions
    ↓
3. Generate/adapt visuals:
   - 9:16 aspect ratio (1080×1920)
   - High contrast, bold text
   - Trending aesthetics
    ↓
4. Add captions/text overlays
    ↓
5. Publish via Douyin API
    ↓
6. Return post URL and video_id
```

## API Usage (To be implemented)

```python
# Pseudocode for Douyin API
# Note: Actual API endpoints depend on Douyin Open Platform

async def publish_to_douyin(
    title: str,
    content_type: str,  # "image_text" or "video"
    media_files: List[str],
    caption: str,
    music_id: Optional[str],
    credentials: Dict
) -> Dict:
    """
    Publish content to Douyin
    
    Args:
        title: Attention-grabbing title
        content_type: "image_text" or "video"
        media_files: List of image paths or video path
        caption: Caption text with hashtags
        music_id: Optional trending music ID
        credentials: {app_id, app_secret, access_token}
    
    Returns:
        {video_id, url, status}
    """
    pass
```

## Content Templates

### Template 1: Tool Discovery (图文)
```
Slide 1: [Shocking statement]
"🔥 这个工具让我震惊了！"

Slide 2: [Problem]
"以前[做某事]要[时间/难度]"

Slide 3: [Solution revealed]
"现在只需要[简单动作]"

Slide 4: [Proof/Result]
"[时间]后，[惊人结果]"

Slide 5: [CTA]
"想要？评论区见"
```

### Template 2: Tutorial (视频)
```
0-3s: "别再做[旧方法]了！"
3-10s: "教你一个更快的方法"
10-30s: [Step by step demo]
30-50s: [Show results]
50-60s: "学会了吗？双击关注"
```

### Template 3: Before/After
```
Slide 1: "Before vs After"
Slide 2: [Before state - struggling]
Slide 3: [The change/tool]
Slide 4: [After state - success]
Slide 5: "你也可以！"
```

## Success Criteria

- ✅ Title creates suspense/curiosity
- ✅ Content adapted to 3-5 slides (图文) or 30-60s script (视频)
- ✅ Visuals in 9:16 ratio (1080×1920)
- ✅ Bold text overlays added
- ✅ Music suggestion provided
- ✅ Strong CTA in final slide/seconds
- ✅ Published via API
- ✅ Post URL returned

## Important Notes

1. **Algorithm**: Douyin algorithm favors watch time and engagement
2. **Trending**: Use trending music and effects when possible
3. **First 3 Seconds**: Critical for retention - must hook immediately
4. **Call to Action**: Always end with clear CTA (comment, follow, etc.)
5. **Consistency**: Regular posting schedule helps with algorithm

## Future Enhancements

- [ ] Auto-trending music suggestions
- [ ] Video script generation from article
- [ ] Auto-caption generation
- [ ] Best posting time analysis
- [ ] Engagement analytics
- [ ] Trending hashtag suggestions

## Related Skills

- `wechat-publisher`: WeChat Official Account publishing
- `xiaohongshu-publisher`: Xiaohongshu publishing
- `wechat-wiki-archiver`: Source content extraction and optimization

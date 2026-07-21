---
name: xiaohongshu-publisher
description: Publish articles to Xiaohongshu (小红书) platform with optimized formatting for the platform's unique style. Handles content adaptation, image generation, and API publishing.
triggers:
  - User wants to publish to Xiaohongshu
  - User says "发小红书"
  - User mentions xiaohongshu or 小红书 publishing
  - Batch publishing to multiple platforms including Xiaohongshu
---

# Xiaohongshu (小红书) Publisher

## Overview

Dedicated skill for publishing content to Xiaohongshu platform. Adapts content to fit Xiaohongshu's unique style:
- Short, punchy titles (max 20 characters recommended)
- Emoji-rich content
- Hashtag-heavy formatting (#标签)
- Square or 3:4 aspect ratio images (recommended 1242×1660)
- Conversational, personal tone
- Focus on lifestyle, tips, and personal experience

## Platform Characteristics

### Content Style
- **Title**: Short, catchy, with emojis (e.g., "🔥这个AI工具让我效率翻倍！")
- **Format**: Short paragraphs, heavy emoji usage
- **Hashtags**: 3-5 relevant tags at the end (e.g., #AI工具 #效率神器 #打工人必备)
- **Tone**: Personal, conversational, like sharing with friends
- **Length**: 300-800 characters optimal (can be longer but may be truncated)

### Image Requirements
- **Ratio**: 3:4 (portrait) or 1:1 (square) recommended
- **Size**: 1242×1660px (3:4) or 1080×1080px (1:1)
- **Style**: Bright, aesthetic, lifestyle-oriented
- **Text on image**: Can have minimal text overlay

### API Requirements
- Xiaohongshu Open Platform API (小红书开放平台)
- Requires: app_id, app_secret, access_token
- Content must comply with platform guidelines

## User Configuration

To be configured when user provides credentials:
- **App ID**: From Xiaohongshu Open Platform
- **App Secret**: From Xiaohongshu Open Platform
- **Access Token**: OAuth2 token for publishing

## Content Adaptation Rules

### Title Adaptation
```
WeChat Title: "不会写代码也能做应用？我试了这个工具，30分钟搞定一个完整项目"
↓
Xiaohongshu Title: "🔥30分钟做出一个App！零代码神器"

Rules:
- Add relevant emojis (🔥💡✨🚀💪)
- Shorten to 20 characters max
- Make it punchy and curiosity-driven
- Use numbers when possible
```

### Content Adaptation
```
Original: Long paragraphs with detailed explanations
↓
Xiaohongshu Format:

姐妹们！发现个宝藏工具💎

不用写代码！真的！
我说了一句话...
30分钟后👇
一个完整应用就上线了！🚀

✨ 核心功能：
• 语音输入需求
• AI自动写代码
• 自动测试部署

💡 适合谁：
✅ 有想法但不会代码
✅ 想快速验证创意
✅ 讨厌写代码的宝子

亲测有效！快去试试～

#AI工具 #零代码 #效率神器 #创业必备 #打工人福音
```

### Hashtag Strategy
- Use 3-5 hashtags at the end
- Mix of broad and specific tags
- Include trending tags when relevant
- Examples:
  - #AI工具 #人工智能 #效率提升
  - #自媒体 #内容创作 #爆款秘籍
  - #打工人 #职场技能 #升职加薪

## Publishing Workflow

```
User provides article
    ↓
1. Extract core content and value proposition
    ↓
2. Adapt title for Xiaohongshu (short + emoji)
    ↓
3. Reformat content:
   - Short paragraphs (2-3 lines max)
   - Add emojis throughout
   - Use bullet points (•)
   - Add personal touches ("姐妹们", "宝子们", "亲测")
    ↓
4. Generate/adapt cover image (3:4 ratio, 1242×1660)
    ↓
5. Add relevant hashtags (3-5 tags)
    ↓
6. Publish via Xiaohongshu API
    ↓
7. Return post URL and post_id
```

## API Usage (To be implemented)

```python
# Pseudocode for Xiaohongshu API
# Note: Actual API endpoints and methods depend on Xiaohongshu Open Platform documentation

async def publish_to_xiaohongshu(
    title: str,
    content: str,
    images: List[str],
    hashtags: List[str],
    credentials: Dict
) -> Dict:
    """
    Publish content to Xiaohongshu
    
    Args:
        title: Short title with emojis
        content: Formatted content with emojis and line breaks
        images: List of image paths (3:4 ratio recommended)
        hashtags: List of hashtag strings
        credentials: {app_id, app_secret, access_token}
    
    Returns:
        {post_id, url, status}
    """
    pass
```

## Content Templates

### Template 1: Tool Discovery
```
🔥 [工具名称] 真的太好用了！

姐妹们！最近挖到个宝藏[工具类型]💎

[一句话描述痛点]

用了这个之后👇
[具体效果/改变]

✨ 我最喜欢的地方：
• [优点1]
• [优点2]  
• [优点3]

💡 适合这样的宝子：
✅ [人群1]
✅ [人群2]
✅ [人群3]

亲测有效！不踩雷！

#[标签1] #[标签2] #[标签3]
```

### Template 2: Tutorial/Tips
```
💡 [数字]个步骤，[达成效果]

很多姐妹问我[问题]...
今天一次性讲清楚！👇

Step 1️⃣: [步骤1]
[简单说明]

Step 2️⃣: [步骤2]
[简单说明]

Step 3️⃣: [步骤3]
[简单说明]

⚠️ 注意事项：
• [注意点1]
• [注意点2]

收藏起来慢慢看！

#[标签1] #[标签2] #[标签3]
```

### Template 3: Personal Experience
```
✨ [时间/经历]后，我[变化]

从[之前状态]到[现在状态]
我只做了这一件事👇

[核心方法/工具]

具体怎么做：
1️⃣ [步骤1]
2️⃣ [步骤2]
3️⃣ [步骤3]

💪 坚持[时间]，你会看到变化！

#[标签1] #[标签2] #[标签3]
```

## Success Criteria

- ✅ Title adapted for Xiaohongshu (short, emoji, punchy)
- ✅ Content reformatted (short paragraphs, emojis, bullets)
- ✅ Hashtags added (3-5 relevant tags)
- ✅ Images adapted (3:4 or 1:1 ratio)
- ✅ Personal tone applied ("姐妹们", "宝子们")
- ✅ Published via API
- ✅ Post URL returned

## Important Notes

1. **Content Compliance**: Must follow Xiaohongshu community guidelines
2. **Image Quality**: High-quality, aesthetic images perform better
3. **Posting Time**: Consider optimal posting times for engagement
4. **Hashtag Research**: Use trending and relevant hashtags
5. **Interaction**: Plan for comment responses and engagement

## Future Enhancements

- [ ] Auto-hashtag suggestion based on content
- [ ] Best posting time recommendation
- [ ] Engagement analytics integration
- [ ] Batch scheduling for multiple posts
- [ ] A/B testing for different titles/formats

## Related Skills

- `wechat-publisher`: WeChat Official Account publishing
- `douyin-publisher`: Douyin (TikTok) publishing
- `wechat-wiki-archiver`: Source content extraction and optimization

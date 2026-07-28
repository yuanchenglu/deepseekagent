/**
 * 会话导出压缩器
 * 将完整会话历史压缩为结构化的导出格式
 */

import { ChatContextCompressor } from './index'
import type { ChatMessage, CompressedResult } from './index'

export class ExportCompressor {
  private compressor: ChatContextCompressor

  constructor() {
    this.compressor = new ChatContextCompressor()
  }

  async compress(
    messages: ChatMessage[],
    upstream: string,
    apiKey: string | undefined,
    sessionId: string,
    opts?: { profile?: string; model?: string | null; provider?: string | null },
  ): Promise<CompressedResult> {
    return this.compressor.compress(messages, upstream, apiKey, sessionId, opts)
  }
}

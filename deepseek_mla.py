import torch
import torch.nn as nn
import torch.nn.functional as F

class DeepSeekMLA(nn.Module):
    def __init__(self, embed_dim, num_heads, kv_heads, dropout=0.0):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.kv_heads = kv_heads
        self.head_dim = embed_dim // num_heads
        
        # 计算kv头与q头的比例
        self.q_per_kv = num_heads // kv_heads
        
        # 投影层
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim // self.q_per_kv)
        self.v_proj = nn.Linear(embed_dim, embed_dim // self.q_per_kv)
        self.o_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, attn_mask=None):
        batch_size, seq_len, _ = x.shape
        
        # 投影到查询、键、值空间
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # 重塑查询头
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 重塑键值头
        k = k.view(batch_size, seq_len, self.kv_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.kv_heads, self.head_dim).transpose(1, 2)
        
        # 扩展键值头以匹配查询头数量
        k = k.repeat_interleave(self.q_per_kv, dim=1)
        v = v.repeat_interleave(self.q_per_kv, dim=1)
        
        # 计算注意力分数
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # 应用注意力掩码
        if attn_mask is not None:
            attn_scores = attn_scores.masked_fill(attn_mask == 0, float('-inf'))
        
        # 计算注意力权重
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 应用注意力权重到值
        attn_output = torch.matmul(attn_weights, v)
        
        # 重塑输出
        attn_output = attn_output.transpose(1, 2).reshape(batch_size, seq_len, self.embed_dim)
        
        # 最终投影
        output = self.o_proj(attn_output)
        
        return output

class TraditionalMHA(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout=0.0):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        # 投影层
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.o_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, attn_mask=None):
        batch_size, seq_len, _ = x.shape
        
        # 投影到查询、键、值空间
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # 重塑头
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力分数
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # 应用注意力掩码
        if attn_mask is not None:
            attn_scores = attn_scores.masked_fill(attn_mask == 0, float('-inf'))
        
        # 计算注意力权重
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 应用注意力权重到值
        attn_output = torch.matmul(attn_weights, v)
        
        # 重塑输出
        attn_output = attn_output.transpose(1, 2).reshape(batch_size, seq_len, self.embed_dim)
        
        # 最终投影
        output = self.o_proj(attn_output)
        
        return output

# 测试代码
if __name__ == "__main__":
    # 创建输入
    batch_size = 2
    seq_len = 10
    embed_dim = 512
    num_heads = 8
    kv_heads = 2
    
    x = torch.randn(batch_size, seq_len, embed_dim)
    
    # 创建模型
    mla = DeepSeekMLA(embed_dim, num_heads, kv_heads)
    mha = TraditionalMHA(embed_dim, num_heads)
    
    # 前向传播
    output_mla = mla(x)
    output_mha = mha(x)
    
    print(f"输入形状: {x.shape}")
    print(f"MLA输出形状: {output_mla.shape}")
    print(f"MHA输出形状: {output_mha.shape}")
    
    # 计算参数数量
    def count_parameters(model):
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"MLA参数数量: {count_parameters(mla)}")
    print(f"MHA参数数量: {count_parameters(mha)}")
    
    # 计算内存使用
    def calculate_memory(model, input_shape):
        batch_size, seq_len, embed_dim = input_shape
        total_memory = 0
        
        # 输入内存
        total_memory += batch_size * seq_len * embed_dim * 4  # 4 bytes per float32
        
        # 投影层内存
        for name, param in model.named_parameters():
            if 'proj' in name:
                total_memory += param.numel() * 4
        
        # 中间激活内存
        if isinstance(model, DeepSeekMLA):
            # MLA中间激活
            num_heads = model.num_heads
            kv_heads = model.kv_heads
            head_dim = model.head_dim
            
            # Q, K, V 内存
            total_memory += batch_size * num_heads * seq_len * head_dim * 4  # Q
            total_memory += batch_size * kv_heads * seq_len * head_dim * 4  # K
            total_memory += batch_size * kv_heads * seq_len * head_dim * 4  # V
            
            # 注意力分数和权重内存
            total_memory += batch_size * num_heads * seq_len * seq_len * 4  # 注意力分数
            total_memory += batch_size * num_heads * seq_len * seq_len * 4  # 注意力权重
            
            # 输出内存
            total_memory += batch_size * seq_len * embed_dim * 4  # 输出
        else:
            # MHA中间激活
            num_heads = model.num_heads
            head_dim = model.head_dim
            
            # Q, K, V 内存
            total_memory += batch_size * num_heads * seq_len * head_dim * 4  # Q
            total_memory += batch_size * num_heads * seq_len * head_dim * 4  # K
            total_memory += batch_size * num_heads * seq_len * head_dim * 4  # V
            
            # 注意力分数和权重内存
            total_memory += batch_size * num_heads * seq_len * seq_len * 4  # 注意力分数
            total_memory += batch_size * num_heads * seq_len * seq_len * 4  # 注意力权重
            
            # 输出内存
            total_memory += batch_size * seq_len * embed_dim * 4  # 输出
        
        return total_memory / (1024 * 1024)  # 转换为MB
    
    input_shape = (batch_size, seq_len, embed_dim)
    mla_memory = calculate_memory(mla, input_shape)
    mha_memory = calculate_memory(mha, input_shape)
    
    print(f"MLA内存使用: {mla_memory:.2f} MB")
    print(f"MHA内存使用: {mha_memory:.2f} MB")
    print(f"内存节省: {(1 - mla_memory/mha_memory) * 100:.2f}%")
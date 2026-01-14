class RNG:
    def __init__(self, seed):
        self.m_w = 123456789
        self.m_z = 987654321
        self.mask = 0xffffffff
        
        self.m_w = (123456789 + seed) & self.mask
        self.m_z = (987654321 - seed) & self.mask

    def random(self, max_val=1, min_val=0):
        # Python handles large integers automatically, but we need to emulate 32-bit wrapping 
        # to match the JS behavior if we want 1:1 deterministic results with JS version.
        # JS bitwise operators truncate to 32 bits.
        
        self.m_z = (36969 * (self.m_z & 65535) + (self.m_z >> 16)) & self.mask
        self.m_w = (18000 * (self.m_w & 65535) + (self.m_w >> 16)) & self.mask
        
        # ((this.m_z << 16) + (this.m_w & 65535)) >>> 0
        # In Python, we need to enforce unsigned 32-bit integer behavior manually for the final result
        result = ((self.m_z << 16) + (self.m_w & 65535)) & 0xFFFFFFFF
        
        result /= 4294967296
        
        return (max_val - min_val) * result + min_val

// Exact nonnegative coefficient convolution via Kronecker substitution.
// Caller selects a byte-aligned radix larger than every convolution coefficient.
// There is no floating-point arithmetic. The exported integer is truncated only
// above the last requested coefficient; lower coefficients are unchanged.
#include <gmp.h>
#include <cstring>
#include <limits>
extern "C" {
const char* packed_gmp_version() { return gmp_version; }
int packed_multiply(const unsigned char* a, size_t an,
                    const unsigned char* b, size_t bn,
                    unsigned char* out, size_t outn) {
  if (!a || !b || !out || !an || !bn || !outn ||
      outn > std::numeric_limits<mp_bitcnt_t>::max()/8) return 1;
  mpz_t x,y,z; mpz_inits(x,y,z,nullptr);
  mpz_import(x,an,-1,1,0,0,a); mpz_import(y,bn,-1,1,0,0,b);
  mpz_mul(z,x,y);
  mpz_fdiv_r_2exp(z,z,(mp_bitcnt_t)outn*8);
  std::memset(out,0,outn); size_t written=0;
  mpz_export(out,&written,-1,1,0,0,z);
  mpz_clears(x,y,z,nullptr);
  return written<=outn ? 0 : 2;
}
}

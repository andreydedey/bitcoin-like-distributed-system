# Padrão de Interoperabilidade - Blockchain LSD 2025

**Equipe:** Andrey Oliveira, Andreya Paiva
**Data:** 03/02/2026

---

## 🎯 Essencial para Comunicação entre Nós

---

## 1. Formato de Transmissão (TCP)

```
[4 bytes: tamanho big-endian] [N bytes: JSON UTF-8]
```

---

## 2. Formato das Mensagens

Todas as mensagens têm esta estrutura:

```json
{
  "type": "<TIPO>",
  "payload": { ... },
  "sender": "host:port"
}
```

### Tipos de mensagem obrigatórios:

| Tipo | Payload |
|------|---------|
| `NEW_TRANSACTION` | `{"transaction": {...}}` |
| `NEW_BLOCK` | `{"block": {...}}` |
| `REQUEST_CHAIN` | `{}` |
| `RESPONSE_CHAIN` | `{"blockchain": {...}}` |

---

## 3. Estrutura de Dados

### Transação
```json
{
  "id": "string-uuid",
  "origem": "string",
  "destino": "string",
  "valor": 10.5,
  "timestamp": 1738627200.123
}
```

### Bloco
```json
{
  "index": 1,
  "previous_hash": "64-char-hex",
  "transactions": [ {...}, {...} ],
  "nonce": 12345,
  "timestamp": 1738627200.5,
  "hash": "64-char-hex"
}
```

### Blockchain (RESPONSE_CHAIN)
```json
{
  "chain": [ {...}, {...} ],
  "pending_transactions": [ {...} ]
}
```

---

## 4. Cálculo do Hash (SHA-256)

**CRÍTICO:** Ordem dos campos deve ser idêntica!

```python
import hashlib, json

block_data = {
    "index": block.index,
    "previous_hash": block.previous_hash,
    "transactions": block.transactions,  # Ordem: id, origem, destino, valor, timestamp
    "nonce": block.nonce,
    "timestamp": block.timestamp
}

hash_hex = hashlib.sha256(
    json.dumps(block_data, sort_keys=True).encode()
).hexdigest()
```

**⚠️ IMPORTANTE:** Usar `sort_keys=True` no JSON!

---

## 5. Bloco Gênesis

**TODOS devem ter este bloco gênesis exato:**

```json
{
  "index": 0,
  "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "transactions": [],
  "nonce": 0,
  "timestamp": 0,
  "hash": "816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7"
}
```

**Teste rápido:**
```bash
python3 -c "import hashlib, json; g = {'index': 0, 'previous_hash': '0'*64, 'transactions': [], 'nonce': 0, 'timestamp': 0}; print(hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest())"
```

Resultado esperado: `816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7`

---

## 6. Recompensa de Mineração

Primeira transação do bloco minerado:

```json
{
  "id": "<uuid-unico>",
  "origem": "coinbase",
  "destino": "<endereco-minerador>",
  "valor": 50.0,
  "timestamp": <timestamp-do-bloco>
}
```

---

## ✅ Checklist

Antes de conectar com outras equipes:

- [ ] Hash do gênesis: `816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7`
- [ ] Hash SHA-256 com `sort_keys=True`
- [ ] Mensagens: `{"type": "...", "payload": {...}, "sender": "..."}`
- [ ] Transmissão: `[4 bytes tamanho big-endian][JSON UTF-8]`
- [ ] Campos obrigatórios de transação e bloco
- [ ] Recompensa "coinbase" de 50


# Guia de Contribuição

Obrigado por considerar contribuir com o **OptiScaler Center**! 🎉

## Como Contribuir

### Reportando Bugs 🐛

Ao reportar bugs, inclua:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Screenshots (se aplicável)
- Informações do sistema:
  - Sistema operacional e versão
  - Versão do Python
  - Versão do OptiScaler Center
  - Log de erro (se disponível)

### Sugerindo Melhorias 💡

Para sugestões de features:
- Descreva claramente a funcionalidade
- Explique por que seria útil
- Forneça exemplos de uso
- Considere possíveis alternativas

### Pull Requests

1. **Fork o Repositório**
   ```bash
   git clone https://github.com/seu-usuario/optiscaler-center.git
   cd optiscaler-center
   ```

2. **Crie um Branch**
   ```bash
   git checkout -b feature/minha-feature
   # ou
   git checkout -b fix/meu-bugfix
   ```

3. **Configure o Ambiente**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   
   pip install -r requirements-dev.txt
   ```

4. **Faça suas Alterações**
   - Siga o estilo de código do projeto
   - Adicione testes se aplicável
   - Atualize documentação se necessário

5. **Execute os Testes**
   ```bash
   pytest tests/
   ```

6. **Verifique o Código**
   ```bash
   # Formatação
   black src/
   
   # Linting
   flake8 src/
   pylint src/
   
   # Type checking
   mypy src/
   ```

7. **Commit suas Mudanças**
   ```bash
   git add .
   git commit -m "Add: descrição da feature"
   ```

   **Convenção de Commits:**
   - `Add:` Nova funcionalidade
   - `Fix:` Correção de bug
   - `Update:` Atualização de código existente
   - `Remove:` Remoção de código
   - `Docs:` Mudanças em documentação
   - `Style:` Formatação, sem mudança de lógica
   - `Refactor:` Refatoração de código
   - `Test:` Adição ou correção de testes
   - `Chore:` Tarefas de manutenção

8. **Push para o Branch**
   ```bash
   git push origin feature/minha-feature
   ```

9. **Abra um Pull Request**
   - Descreva as mudanças claramente
   - Referencie issues relacionadas
   - Inclua screenshots se for mudança visual

## Estilo de Código

### Python (PEP 8)

- Use **4 espaços** para indentação
- Máximo de **88 caracteres** por linha (Black)
- Use **type hints** sempre que possível
- Docstrings em **formato Google**

Exemplo:
```python
def minha_funcao(param1: str, param2: int = 0) -> bool:
    """
    Breve descrição da função.
    
    Args:
        param1: Descrição do parâmetro 1
        param2: Descrição do parâmetro 2
    
    Returns:
        Descrição do retorno
    
    Raises:
        ValueError: Quando param1 é inválido
    """
    # Implementação
    return True
```

### Arquitetura

- Siga os princípios de **Clean Architecture**
- Mantenha separação clara entre camadas:
  - **Presentation**: UI/Interface
  - **Application**: Casos de uso
  - **Domain**: Lógica de negócio
  - **Infrastructure**: Serviços externos

- Use **dependency injection**
- Evite dependências circulares
- Mantenha classes e funções pequenas e focadas

### Git

- Commits pequenos e focados
- Mensagens claras e descritivas
- Um commit por mudança lógica
- Rebase antes de abrir PR (se necessário)

## Estrutura de Testes

```python
# tests/unit/test_game_scanner.py
import pytest
from application.services.game_scanner import GameScanner

class TestGameScanner:
    """Testes para o GameScanner"""
    
    @pytest.fixture
    def scanner(self):
        """Fixture para criar um scanner"""
        return GameScanner()
    
    def test_detect_steam_path(self, scanner):
        """Testa detecção do path do Steam"""
        path = scanner.detect_steam_path()
        assert path is not None
        assert path.exists()
```

## Revisão de Código

Todos os PRs passarão por revisão. O revisor verificará:

- ✅ Código segue os padrões do projeto
- ✅ Testes passam
- ✅ Documentação atualizada
- ✅ Sem warnings de linting
- ✅ Performance adequada
- ✅ Segurança (sem vulnerabilidades)

## Dúvidas?

- Abra uma **Discussion** no GitHub
- Entre em contato via **Issues**

## Código de Conduta

Este projeto segue o [Contributor Covenant](https://www.contributor-covenant.org/).
Esperamos que todos os participantes sejam respeitosos e profissionais.

### Comportamentos Esperados

- ✅ Ser respeitoso e inclusivo
- ✅ Aceitar críticas construtivas
- ✅ Focar no que é melhor para a comunidade
- ✅ Mostrar empatia com outros membros

### Comportamentos Inaceitáveis

- ❌ Assédio ou discriminação
- ❌ Comentários ofensivos
- ❌ Ataques pessoais
- ❌ Trolling ou comentários provocativos

## Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença MIT do projeto.

---

**Obrigado por contribuir! 🚀**

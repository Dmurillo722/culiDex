## Setup

### First-Time Setup

1. Navigate to the project directory

2. Activate/create python virtual environment

3. Install maturin
```bash
   pip install maturin
```

4. Initialize maturin — select **pyo3** when prompted
```bash
   maturin init
```

5. Run this command for initialization and when modifying:

```bash
maturin develop
```


---

### Development

After modifying Rust code, rerun this command:

```bash
maturin develop
```
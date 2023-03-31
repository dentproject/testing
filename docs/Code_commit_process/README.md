# Test prerequisite for Code Commit

![Dent-SIT](../img/code_commit.png)

To run the pre-commit checks locally, you can follow below steps:

- Ensure that default python is python3.

- Ensure that the `pre-commit` package is installed:

```Shell
sudo pip install pre-commit
```

- Go to repository root folder

- Install the pre-commit hooks:

```Shell
pre-commit install
```

- Use pre-commit to check staged file:

```Shell
pre-commit
```

- Alternatively, you can check committed files using:

```Shell
pre-commit run --from-ref <commit_id> --to-ref <commit_id>
# or
pre-commit run --all-files
```

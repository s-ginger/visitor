@echo off

hf upload %1 ./data . --repo-type dataset

if errorlevel 1 (
    echo Upload failed.
) else (
    echo Upload completed successfully.
)

pause
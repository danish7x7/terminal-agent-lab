FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
RUN mkdir -p /project/src/lib /project/src/bin /project/src/config /project/src/tests /output /staging /verify

# Regular source files (recent mtime)
RUN echo 'def hello(): pass' > /project/src/lib/utils.py && touch -t 202403010000 /project/src/lib/utils.py
RUN echo 'def parse(): pass' > /project/src/lib/parser.py && touch -t 202405150000 /project/src/lib/parser.py
RUN printf '%0.s#' {1..100} > /project/src/lib/helpers.py && touch -t 202406010000 /project/src/lib/helpers.py
RUN echo 'main entrypoint' > /project/src/bin/run.sh && touch -t 202404010000 /project/src/bin/run.sh
RUN echo 'version=1.0' > /project/src/config/settings.cfg && touch -t 202407010000 /project/src/config/settings.cfg
RUN echo 'debug=false' > /project/src/config/prod.cfg && touch -t 202407020000 /project/src/config/prod.cfg
RUN echo 'import utils' > /project/src/tests/test_utils.py && touch -t 202405010000 /project/src/tests/test_utils.py

# Files that should be EXCLUDED because mtime < 2024-01-01
RUN echo 'old code here' > /project/src/lib/legacy.py && touch -t 202312010000 /project/src/lib/legacy.py
RUN echo 'ancient config' > /project/src/config/old.cfg && touch -t 202301010000 /project/src/config/old.cfg

# Files that should be EXCLUDED because size > 2048 bytes
RUN python3 -c "print('x'*3000)" > /project/src/lib/bigfile.py && touch -t 202406010000 /project/src/lib/bigfile.py
RUN python3 -c "print('y'*4000)" > /project/src/bin/bigbin.sh && touch -t 202406010000 /project/src/bin/bigbin.sh

# Files that should be EXCLUDED because *.tmp or *.log
RUN echo 'temp data' > /project/src/tests/scratch.tmp && touch -t 202406010000 /project/src/tests/scratch.tmp
RUN echo 'build log' > /project/src/build.log && touch -t 202406010000 /project/src/build.log
RUN echo 'another tmp' > /project/src/config/cache.tmp && touch -t 202407010000 /project/src/config/cache.tmp

# Symlinks pointing to real files (should be dereferenced and included)
RUN ln -s /project/src/lib/utils.py /project/src/lib/utils_link.py
RUN ln -s /project/src/config/settings.cfg /project/src/config/settings_link.cfg

# Symlink pointing to a file that will be excluded (big); dereferenced copy would also be excluded by size rule
RUN ln -s /project/src/lib/bigfile.py /project/src/lib/bigfile_link.py

# Dangling symlink — must be skipped
RUN ln -s /project/src/nonexistent.py /project/src/lib/dangling_link.py

# A symlink to a file old enough to be excluded by mtime rule
RUN ln -s /project/src/lib/legacy.py /project/src/lib/legacy_link.py

WORKDIR /app

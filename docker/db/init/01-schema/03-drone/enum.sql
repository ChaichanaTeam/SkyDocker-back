create type drone_category as enum (
    'pb',
    'c0',
    'c1',
    'c2',
    'c3',
    'c4',
    'c5',
    'c6'
);

COMMENT ON TYPE drone_category IS 'PB, C0 - C4 are mainly categorized for open operational category, else is specific;
                                  PB stands for private build';

schema1 = {
  "$id": "https://example.com/movie.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a movie",
  "type": "object",
  "required": ["title", "director", "releaseDate"],
  "properties": {
    "title": {
      "type": "string"
    },
    "director": {
      "type": "string"
    },
    "releaseDate": {
      "type": "string",
      "format": "date"
    },
    "genre": {
      "type": "string",
      "enum": ["Action", "Comedy", "Drama", "Science Fiction"]
    },
    "duration": {
      "type": "string"
    },
    "cast": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "additionalItems": false
    }
  }
}


schema2 = {
  "$id": "https://example.com/job-posting.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a job posting",
  "type": "object",
  "required": ["title", "company", "location", "description"],
  "properties": {
    "title": {
      "type": "string"
    },
    "company": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "employmentType": {
      "type": "string"
    },
    "salary": {
      "type": "number",
      "minimum": 0
    },
    "applicationDeadline": {
      "type": "string",
      "format": "date"
    }
  }
}


store: dict[float, dict] = dict()
store[(1.0, 'schema1')] = schema1
store[(1.2, 'schema2')] = schema1

stores: dict[str, dict] = {}
stores['reha'] = store

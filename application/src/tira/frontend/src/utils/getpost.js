export const submitPost = async (url, csrf, params) => {
    const headers = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
    })
    console.log(JSON.stringify(params))
    const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(params)
    })
    if (!response.ok) {
        throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status === 1) {
        throw new Error(`${results.message}`);
    }
    return results
}

export const get = async (url) => {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status === 1) {
      throw new Error(`${results.message}`);
    }
    return results
}
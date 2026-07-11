import assert from 'node:assert/strict'

const { isAnonymousPageAllowed, parseUserSession, userLoginPath } = await import('../src/utils/auth.ts')

assert.deepEqual(parseUserSession('{"id":7,"email":"test@example.com","display_name":"星河海豚·4821","token":"abc"}'), {
  id: 7,
  email: 'test@example.com',
  display_name: '星河海豚·4821',
  token: 'abc',
})
assert.equal(parseUserSession('{"id":7,"email":"test@example.com","token":"abc"}')?.display_name, 'test@example.com')
assert.equal(parseUserSession('{broken'), null)
assert.equal(isAnonymousPageAllowed(2, ''), true)
assert.equal(isAnonymousPageAllowed(3, ''), false)
assert.equal(isAnonymousPageAllowed(3, 'token'), true)
assert.equal(userLoginPath('/jobs?source=tencent'), '/login?from=%2Fjobs%3Fsource%3Dtencent')

console.log('userAuth tests passed')

package de.webis.tira.client.web.authentication;

import javax.servlet.http.HttpServletRequest;

import org.junit.Assert;
import org.junit.Test;
import org.mockito.Matchers;
import org.mockito.Mockito;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;

public class AuthenticatorTest {
	
	@Test
	public void testThatNullRequestIsNotSignedIn() throws Exception {
		HttpServletRequest request = request(null, null);
		
		Assert.assertFalse(Authenticator.isSignedIn(request));
		Assert.assertNull(Authenticator.signedInUser(request));
	}
	
	@Test
	public void testThatRequestWithGroupAndWithoutUserIsNotSignedIn() throws Exception {
		HttpServletRequest request = request(null, "vm-xyz");
		
		Assert.assertFalse(Authenticator.isSignedIn(request));
		Assert.assertNull(Authenticator.signedInUser(request));
	}
	
	@Test
	public void testThatRequestWithUserAndWithoutGroupIsSignedIn() throws Exception {
		HttpServletRequest request = request("foo-bar", null);
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	@Test
	public void testThatRequestWithUserAndWithGroupIsSignedIn() throws Exception {
		HttpServletRequest request = request("foo-bar", "vm-foo-bar");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	@Test
	public void testThatRequestWithUserAndWithAdminGroupUsesTheAdminGroup() throws Exception {
		HttpServletRequest request = request("foo-bar", "vm-froebe");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
	}

	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup2() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe,fdghdf");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup3() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe,vm-foobar,fdghdf");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup4() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsavm-foobar,,vm-froebe,fdghdf");
		
		Assert.assertTrue(Authenticator.isSignedIn(request));
		User user = Authenticator.signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	private static HttpServletRequest request(String userName, String groups) {
		HttpServletRequest ret = Mockito.mock(HttpServletRequest.class);
		
		Mockito.when(ret.getHeader(Matchers.anyString())).then(new Answer<String>() {
			@Override
			public String answer(InvocationOnMock i) throws Throwable {
				String arg = i.getArgumentAt(0, String.class);
				
				if(userName != null && "X-Disraptor-User".equals(arg)) {
					return userName;
				} else if (groups != null && "X-Disraptor-Groups".equals(arg)){
					return groups;
				} else {
					return null;
				}
			}
		});
		
		return ret;
	}
}

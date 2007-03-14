<?python
layout_params['displayNotes']=True
TODO='Not yet implemented'
?>
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://purl.org/kid/ns#"
  py:layout="'layout.kid'">
<div py:match="item.tag == 'content'">
  <script type='text/javascript'
    src="${tg.url('/static/javascript/framework.js')}"></script>
  <script type='text/javascript'
    src="${tg.url('/static/javascript/pkgpage.js')}"></script>
  <h1 py:content="package.name">Package</h1>
  <table border="0">
    <tr><td>
      Status
    </td><td py:content="package.statusname">
    </td></tr>
    <tr><td>
      Creation Date
    </td><td py:content="TODO">
      Fill in the Creation Date
    </td></tr>
  </table>
  <p py:content="package.summary">Summary</p>
  <p py:content="package.description">Description</p>

  <p>Contents:
    <ul py:for="pkg in packageListings">
      <li><a py:attrs="{'href' : ''.join(
         ('#', pkg.collection.name, pkg.collection.version)).replace(' ','')}"
        py:content="' '.join((pkg.collection.name, pkg.collection.version))">
      </a></li>
    </ul>
  </p>
  <form action="${tg.url('/packages/dispatcher/')}" method="POST">
  <table class="pkglist" py:for="pkg in packageListings"
    py:attrs="{'name': str(pkg.id)}">
    <tr><th>
      Collection
    </th><th>
      Owner
    </th><th>
      QA Contact
    </th><th>
      Status
    </th></tr>
    <tr id="${''.join((pkg.collection.name, pkg.collection.version)).replace(' ','')}">
      <td><a href="${tg.url('/collections/id/' + str(pkg.collection.id))}"
        py:content="' '.join((pkg.collection.name, pkg.collection.version))"></a>
      </td><td>
        <div py:if="pkg.ownerid == 9900"
          py:attrs="{'name': str(pkg.id)}"
          class="requestContainer owner orphaned">
          <span class="ownerName">${pkg.ownername}</span>
        <span py:if="pkg.ownerid == 9900">
          <span py:if="'cvsextras' in tg.identity.groups and pkg.collection.status.translations[0].statusname!='EOL'">
            <input type="button" name="unorphan"
              class="ownerButton unorphanButton"
              value="Take Ownership"></input>
          </span>
        </span>
        </div>
        <div py:if="pkg.ownerid != 9900"
          py:attrs="{'name': str(pkg.id)}"
          class="requestContainer owner owned">
          <span class="ownerName">${pkg.ownername}</span>
        <span py:if="not tg.identity.anonymous and tg.identity.user.user_id == pkg.ownerid">
          <input type="button" name="orphan"
            class="ownerButton orphanButton"
            value="Release Ownership"/>
        </span>
        </div>
      </td><td py:content="pkg.qacontactname">
      </td><td py:content="pkg.status.translations[0].statusname">
      </td></tr>
    <tr py:if="not tg.identity.anonymous or pkg.people" colspan="4"><td colspan="4">
      <table class="acls" width="100%">
        <tr>
          <th py:for="colName in ['User'] + list(aclNames)" py:content="colName">
          </th>
        </tr>
        <tr py:for="person in pkg.people" class="aclrow">
          <td py:content="person.name" class="acluser"
            py:attrs="{'name': str(pkg.id) + ':' + str(person.userid)}">
            Name
          </td>
          <td py:for="acl in aclNames" class="aclcell">
            <!-- If the logged in user is this row, add a checkbox to set it -->
            <div py:if="not tg.identity.anonymous and
              person.userid==tg.identity.user.user_id"
              py:attrs="{'name' : str(pkg.id) + ':' + acl}"
              class="requestContainer aclPresent">
              <input type="checkbox" checked="true" class="aclPresentBox"
                py:if="person.aclOrder[acl]"/>
              <input type="checkbox" class="aclPresentBox"
                py:if="not person.aclOrder[acl]"/>
            </div>
          </td>
        </tr>
<!--
-->
            <!-- If the user can set acls, give drop downs for status -->
<!--
            <div py:if="not tg.identity.anonymous and (
              tg.identity.user.user_id==pkg.ownerid or
              (tg.identity.user.user_id in pkg.people and 
                pkg.people[tg.identity.user.user_id].aclOrder.has_key('approveacls')
                and pkg.people[tg.identity.user.user_id].aclOrder['approveacls'].translations[0].statusname=='Approved'))"
              py:attrs="{'name': str(pkg.id) + ':' + acl}"
                class='aclStatus requestContainer'>
              <select class="aclStatusList">
                <span py:for="status in aclStatus">
                  <option selected="true"
                    py:if="person.aclOrder[acl].translations[0].statusname==status"
                    py:content="status"
                    py:attrs="{'value': status,
                    'name': status}"></option>
                  <option py:if="not person.aclOrder[acl].translations[0].statusname==status"
                    py:content="status"
                    py:attrs="{'value': status,
                    'name': status}"></option>
                </span>
              </select>
            </div>
            <span py:if="tg.identity.anonymous or
              (tg.identity.user.user_id != pkg.ownerid and
              (tg.identity.user.user_id not in pkg.people or
                pkg.people[tg.identity.user.user_id].aclOrder['approveacls'].translations[0].statusname!='Approved'))"
              py:content="person[1].acls[acl]" 
              py:attrs="{'name' : acl}" class="aclStatus"></span>
          </td>
        </tr>

        <tr py:for="group in pkg.groups" class="aclgrouprow">
          <td py:content="group.name" class="aclgroup"
            py:attrs="{'name': str(pkg.id) + ':' + str(group.groupid)}">
            Name
          </td>
-->
          <!-- If the user has permission to edit the acls, give them a
               checkbox to edit this
            -->
<!--
          <td class="acell" py:attrs="{'colspan' : str(len(aclNames))}">
            <div py:if="not tg.identity.anonymous and
              pkg.ownerid==tg.identity.user.user_id"
              py:attrs="{'name' : str(pkg.id) + ':groupcommit'}"
              class="requestContainer groupAclPresent">
              <input type="checkbox" checked="true" class="groupAclPresentBox"
                py:if="group.aclOrder['commit'].translations[0].statusname=='Approved'"/>
              <input type="checkbox" class="aclPresentBox"
                py:if="not group.aclOrder['commit'].translations[0].statusname!='Approved'"/>
            Allow anyone in this group to commit
            </div>
            <span py:if="tg.identity.anonymous or
              (tg.identity.user.user_id != pkg.ownerid and
              (tg.identity.user.user_id not in pkg.people or
                pkg.people[tg.identity.user.user_id].aclOrder['approveacls'].translations[0].statusname!='Approved'))"
              py:content="person[1].acls[acl]" 
              py:attrs="{'name' : acl}" class="aclStatus"></span>
          </td>
        </tr>
        <tr py:if="not tg.identity.anonymous and
          tg.identity.user.user_id not in pkg.people">
          <td class="acladd" py:attrs="{'colspan' : str(len(aclNames)+1)}">
            <input type="button" py:attrs="{'name':'add:' + str(pkg.package.id)
              + ':' + str(tg.identity.user.user_id)}"
              class="addMyselfButton"
              value="Add myself to package"/>
          </td>
        </tr>
-->
      </table>
    </td></tr>
  </table>
  </form>
  <div id='Notes' py:if="layout_params['displayNotes']">
  <p>
    <ul>
      <li>If the user is an owner or has permission to change packagedb information they can edit all the mutable package information.</li>
      <li>Package name and EVR are immutable.  Status should eventually be immutable (set automatically).</li>
    </ul>
  </p>
  </div>
</div>
</html>
